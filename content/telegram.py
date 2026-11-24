"""Мелочи для Telegram-бота, которые нужны и вне него (без aiogram).

Например, обработка видео (отдельный процесс) сообщает в чат, что отзыв готов.
"""

import logging
from functools import lru_cache

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

SITE_REVIEWS_URL = "https://taza-ayim.kg/ru#reviews"


def _api(method, **params):
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return None
    r = requests.post(f"https://api.telegram.org/bot{token}/{method}", json=params, timeout=15)
    r.raise_for_status()
    return r.json().get("result")


def notify(chat_id, text):
    """Сообщение в чат; ошибки только в лог — сайт от бота не зависит."""
    if not chat_id:
        return
    try:
        _api("sendMessage", chat_id=chat_id, text=text, disable_web_page_preview=True)
    except requests.RequestException as e:
        logger.warning("Не удалось написать в Telegram: %s", e)


@lru_cache(maxsize=1)
def bot_username():
    me = _api("getMe")
    return me["username"] if me else None


def invite_link(code):
    username = bot_username()
    return f"https://t.me/{username}?start={code}" if username else None
