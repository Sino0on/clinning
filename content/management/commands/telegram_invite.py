from django.core.management.base import BaseCommand

from content.models import TelegramInvite
from content.telegram import invite_link


class Command(BaseCommand):
    help = "Одноразовая ссылка-приглашение в Telegram-бота для отзывов"

    def add_arguments(self, parser):
        parser.add_argument("--note", default="", help="Для кого (видно в админке)")

    def handle(self, *args, **options):
        invite = TelegramInvite.objects.create(note=options["note"])
        link = invite_link(invite.code)
        if link:
            self.stdout.write(f"Ссылка для «{invite.note or 'без подписи'}»: {link}")
        else:
            self.stdout.write(
                f"Код приглашения: {invite.code} (ссылку не собрать: не задан TELEGRAM_BOT_TOKEN)"
            )
