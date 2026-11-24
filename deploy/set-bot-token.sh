#!/usr/bin/env bash
# Записывает токен Telegram-бота (от @BotFather) в .env бэкенда и
# перезапускает бота. Токен вводится скрыто и нигде не печатается.
#
# На сервере: /usr/local/bin/clinning-set-bot-token
# Запуск со своего компьютера:
#   ssh -t root@217.114.0.30 clinning-set-bot-token
set -euo pipefail

APP_DIR=/home/projects/clinning
ENV="$APP_DIR/.env"

read -rsp "Вставьте токен от @BotFather и нажмите Enter: " TOKEN
echo
TOKEN=$(printf '%s' "$TOKEN" | tr -d '[:space:]')

if ! [[ "$TOKEN" =~ ^[0-9]{6,}:[A-Za-z0-9_-]{30,}$ ]]; then
  echo "Это не похоже на токен бота (он выглядит как 1234567890:AAH...). Ничего не изменено."
  exit 1
fi

# Проверяем токен у самого Telegram
ME=$(curl -fsS --max-time 15 "https://api.telegram.org/bot${TOKEN}/getMe" || true)
if ! grep -q '"ok":true' <<<"$ME"; then
  echo "Telegram не принял этот токен. Проверьте, что скопировали его целиком. Ничего не изменено."
  exit 1
fi
USERNAME=$(sed -n 's/.*"username":"\([^"]*\)".*/\1/p' <<<"$ME")

mkdir -p /root/backups/clinning
cp -a "$ENV" "/root/backups/clinning/env.$(date +%F-%H%M%S).bak"
sed -i '/^TELEGRAM_BOT_TOKEN=/d' "$ENV"
printf 'TELEGRAM_BOT_TOKEN=%s\n' "$TOKEN" >>"$ENV"

cd "$APP_DIR"
# web тоже: токен нужен ему для ссылок-приглашений в админке и уведомлений
docker compose up -d --no-deps --force-recreate web bot >/dev/null 2>&1
echo "Готово: бот @${USERNAME} запущен."
