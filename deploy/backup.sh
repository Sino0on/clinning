#!/usr/bin/env bash
# Ежедневный бэкап бэкенда: база (pg_dump) и загруженные файлы (media/).
#
# На сервере: /usr/local/bin/clinning-backup, запускается таймером
# clinning-backup.timer каждую ночь. Хранятся последние 14 дней в
# /root/backups/clinning/daily/ГГГГ-ММ-ДД/.
#
# Файлы копируются через rsync --link-dest: каждый день выглядит как полная
# копия, но на диске места занимают только новые и изменённые файлы.
#
# Восстановление базы:
#   zcat /root/backups/clinning/daily/ДАТА/db.sql.gz | \
#     docker compose exec -T db psql -U clinning_user -d clinning
# Восстановление файлов:
#   rsync -a /root/backups/clinning/daily/ДАТА/media/ /home/projects/clinning/media/
#
# ВНИМАНИЕ: бэкап лежит на том же сервере. От ошибок и случайного удаления
# он спасает, от потери сервера — нет.
set -euo pipefail

APP_DIR=/home/projects/clinning
ROOT=/root/backups/clinning/daily
KEEP_DAYS=14
DAY=$(date +%F)
DEST="$ROOT/$DAY"

mkdir -p "$DEST"
cd "$APP_DIR"

docker compose exec -T db pg_dump -U clinning_user -d clinning | gzip >"$DEST/db.sql.gz.tmp"
mv "$DEST/db.sql.gz.tmp" "$DEST/db.sql.gz"

PREV=$(ls -1d "$ROOT"/????-??-?? 2>/dev/null | grep -v "/$DAY$" | tail -1 || true)
if [ -n "$PREV" ] && [ -d "$PREV/media" ]; then
  rsync -a --delete --link-dest="$PREV/media" "$APP_DIR/media/" "$DEST/media/"
else
  rsync -a --delete "$APP_DIR/media/" "$DEST/media/"
fi

# Старше KEEP_DAYS дней — удаляем
ls -1d "$ROOT"/????-??-?? | head -n -"$KEEP_DAYS" | xargs -r rm -rf

echo "[$(date '+%F %T')] Бэкап готов: $DEST ($(du -sh "$DEST" | cut -f1), база $(du -h "$DEST/db.sql.gz" | cut -f1))"
