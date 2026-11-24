"""Telegram-бот для отзывов: отправил фото/видео → «Опубликовать?» → на сайте.

Запуск: python manage.py run_telegram_bot (сервис `bot` в docker-compose).
Токен — TELEGRAM_BOT_TOKEN в .env. Без токена бот спит и не падает.

Доступ только у редакторов (TelegramEditor). Редактор появляется, когда
человек открывает одноразовую ссылку-приглашение:
python manage.py telegram_invite --note "Для кого".

Ограничение Telegram: бот может скачать файл не больше 20 МБ. Обычное видео
Telegram сам сжимает при отправке, поэтому минутный отзыв обычно влезает.
"""

import asyncio
import logging
import tempfile
import time
import uuid
from pathlib import Path

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.utils import timezone

logger = logging.getLogger("content.bot")

SITE_URL = "https://taza-ayim.kg/ru#reviews"
TELEGRAM_FILE_LIMIT = 20 * 1024 * 1024
PENDING_TTL = 6 * 3600  # неподтверждённые отзывы забываем через 6 часов

HELP = (
    "Отправьте сюда фото, скриншот или видео отзыва — я спрошу, публиковать ли его на сайте.\n\n"
    "Подпись к фото или видео можно не писать. Если напишете (например, «Отзыв о генеральной "
    "уборке»), её не будет видно на сайте, но она подскажет Google, что на фото.\n\n"
    "Видео лучше отправлять обычным способом, не «файлом»: так Telegram сам его сожмёт."
)


# ---------- Работа с базой (синхронно, вызывается через sync_to_async) ----------


def _db(fn):
    def wrapper(*args, **kwargs):
        close_old_connections()
        try:
            return fn(*args, **kwargs)
        finally:
            close_old_connections()

    return sync_to_async(wrapper, thread_sensitive=True)


@_db
def is_editor(telegram_id):
    from content.models import TelegramEditor

    return TelegramEditor.objects.filter(telegram_id=telegram_id, is_active=True).exists()


@_db
def accept_invite(code, telegram_id, name):
    """Возвращает True, если по коду дали доступ (или он уже был)."""
    from content.models import TelegramEditor, TelegramInvite

    invite = TelegramInvite.objects.filter(code=code, used_at__isnull=True).first()
    if not invite:
        return TelegramEditor.objects.filter(telegram_id=telegram_id, is_active=True).exists()
    editor, _ = TelegramEditor.objects.update_or_create(
        telegram_id=telegram_id, defaults={"name": name, "is_active": True}
    )
    invite.used_at = timezone.now()
    invite.used_by = editor
    invite.save(update_fields=["used_at", "used_by"])
    return True


@_db
def create_review(path, filename, caption, chat_id):
    from content.models import Review

    with open(path, "rb") as f:
        review = Review(
            caption_ru=caption[:200],
            telegram_chat_id=chat_id,
            is_published=True,
        )
        review.file = File(f, name=filename)
        # Те же проверки, что в админке (формат, размер) — с понятными сообщениями
        review.full_clean()
        review.save()  # фото ужмётся сразу, видео уйдёт в фоновую обработку
    return review.pk, review.kind


@_db
def hide_review(pk):
    from content.models import Review

    return Review.objects.filter(pk=pk).update(is_published=False) > 0


# ---------- Бот ----------


def build_dispatcher():
    from aiogram import F, Router
    from aiogram.dispatcher.dispatcher import Dispatcher
    from aiogram.exceptions import TelegramBadRequest
    from aiogram.filters import CommandObject, CommandStart
    from aiogram.types import (
        CallbackQuery,
        InlineKeyboardButton,
        InlineKeyboardMarkup,
        Message,
    )

    router = Router()
    # token -> {file_id, filename, caption, chat_id, created}
    pending: dict[str, dict] = {}

    def keyboard(*buttons):
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=d) for t, d in buttons]]
        )

    def cleanup():
        now = time.time()
        for k in [k for k, v in pending.items() if now - v["created"] > PENDING_TTL]:
            pending.pop(k, None)

    @router.message(CommandStart(deep_link=True))
    async def start_with_invite(message: Message, command: CommandObject):
        user = message.from_user
        name = " ".join(filter(None, [user.first_name, user.last_name])) or user.username or ""
        if await accept_invite(command.args or "", user.id, name):
            await message.answer(f"Здравствуйте{', ' + user.first_name if user.first_name else ''}! 👋\n\n{HELP}")
        else:
            await message.answer("Ссылка-приглашение недействительна или уже использована.")

    @router.message(CommandStart())
    async def start(message: Message):
        if await is_editor(message.from_user.id):
            await message.answer(HELP)
        else:
            await message.answer(
                "Это служебный бот компании «Таза Айым». Доступ — по приглашению."
            )

    @router.message(F.photo | F.video | F.video_note | F.document)
    async def media(message: Message):
        if not await is_editor(message.from_user.id):
            return await message.answer("Это служебный бот компании «Таза Айым».")

        if message.photo:
            item, filename = message.photo[-1], "telegram.jpg"
        elif message.video:
            item, filename = message.video, message.video.file_name or "telegram.mp4"
        elif message.video_note:
            item, filename = message.video_note, "telegram.mp4"
        else:
            doc = message.document
            mime = doc.mime_type or ""
            if not (mime.startswith("image/") or mime.startswith("video/")):
                return await message.answer("Это не фото и не видео. " + HELP)
            item, filename = doc, doc.file_name or ("file.jpg" if mime.startswith("image/") else "file.mp4")

        if (item.file_size or 0) > TELEGRAM_FILE_LIMIT:
            return await message.answer(
                "Файл больше 20 МБ — Telegram не даёт ботам скачивать такие.\n\n"
                "Отправьте видео обычным способом (не «файлом»), Telegram сам его сожмёт. "
                "Или загрузите его через админку: https://clinning.sino0on.com/admin/"
            )

        cleanup()
        token = uuid.uuid4().hex[:12]
        pending[token] = {
            "file_id": item.file_id,
            "filename": filename,
            "caption": (message.caption or "").strip(),
            "chat_id": message.chat.id,
            "created": time.time(),
        }
        await message.reply(
            "Опубликовать этот отзыв на сайте?",
            reply_markup=keyboard(("✅ Опубликовать", f"pub:{token}"), ("✖️ Отмена", f"no:{token}")),
        )

    @router.message()
    async def other(message: Message):
        if await is_editor(message.from_user.id):
            await message.answer(HELP)
        else:
            await message.answer("Это служебный бот компании «Таза Айым».")

    @router.callback_query(F.data.startswith("no:"))
    async def cancel(call: CallbackQuery):
        pending.pop(call.data[3:], None)
        await call.message.edit_text("Не публикую. Отзыв никуда не отправлен.")
        await call.answer()

    @router.callback_query(F.data.startswith("pub:"))
    async def publish(call: CallbackQuery):
        if not await is_editor(call.from_user.id):
            return await call.answer("Нет доступа", show_alert=True)
        item = pending.pop(call.data[4:], None)
        if not item:
            return await call.answer(
                "Не нашёл этот отзыв — отправьте его ещё раз, пожалуйста.", show_alert=True
            )
        await call.answer("Публикую…")
        await call.message.edit_text("⏳ Загружаю…")

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "upload"
            try:
                await call.bot.download(item["file_id"], destination=path, timeout=120)
            except TelegramBadRequest as e:
                logger.warning("Не удалось скачать файл из Telegram: %s", e)
                return await call.message.edit_text(
                    "Не получилось скачать файл из Telegram (возможно, он больше 20 МБ). "
                    "Загрузите его через админку: https://clinning.sino0on.com/admin/"
                )
            try:
                pk, kind = await create_review(path, item["filename"], item["caption"], item["chat_id"])
            except Exception as e:  # noqa: BLE001 — сообщить человеку, а не молча упасть
                logger.exception("Не удалось сохранить отзыв")
                msg = getattr(e, "messages", None)
                return await call.message.edit_text(
                    "Не удалось сохранить отзыв: " + ("; ".join(msg) if msg else "внутренняя ошибка")
                )

        hide_kb = keyboard(("🙈 Скрыть с сайта", f"hide:{pk}"))
        if kind == "video":
            await call.message.edit_text(
                "⏳ Видео обрабатывается (1–3 минуты). Напишу, когда оно появится на сайте.",
                reply_markup=hide_kb,
            )
        else:
            await call.message.edit_text(
                f"✅ Опубликовано! Через ~10 секунд отзыв будет на сайте:\n{SITE_URL}",
                reply_markup=hide_kb,
                disable_web_page_preview=True,
            )

    @router.callback_query(F.data.startswith("hide:"))
    async def hide(call: CallbackQuery):
        if not await is_editor(call.from_user.id):
            return await call.answer("Нет доступа", show_alert=True)
        ok = await hide_review(int(call.data[5:]))
        await call.message.edit_text(
            "🙈 Скрыто с сайта. Вернуть можно в админке: галочка «Показывать на сайте»."
            if ok
            else "Этот отзыв уже удалён."
        )
        await call.answer()

    dp = Dispatcher()
    dp.include_router(router)
    return dp


class Command(BaseCommand):
    help = "Telegram-бот для публикации отзывов на сайте"

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            # Не падаем в цикле перезапусков: просто ждём, пока задать токен
            self.stdout.write("TELEGRAM_BOT_TOKEN не задан — бот выключен. Задайте токен и перезапустите сервис bot.")
            while True:
                time.sleep(3600)

        from aiogram import Bot

        async def main():
            bot = Bot(token)
            me = await bot.get_me()
            logger.info("Бот @%s запущен", me.username)
            await build_dispatcher().start_polling(bot, allowed_updates=["message", "callback_query"])

        asyncio.run(main())
