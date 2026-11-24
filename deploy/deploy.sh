#!/usr/bin/env bash
# Автодеплой бэкенда clinning.sino0on.com (API текстов сайта taza-ayim.kg).
#
# Работает по принципу pull: systemd-таймер раз в минуту вызывает
# `clinning-deploy check`. Если в origin/main появились новые коммиты, они
# деплоятся. Секреты в GitHub и входящий доступ к серверу не нужны.
#
# На сервере установлен как /usr/local/bin/clinning-deploy (копия этого файла).
# После правок здесь его нужно переустановить:
#   scp deploy/deploy.sh root@217.114.0.30:/usr/local/bin/clinning-deploy
#
# Команды:
#   clinning-deploy check    задеплоить, если в main есть новые коммиты (так делает таймер)
#   clinning-deploy deploy   задеплоить свежий main прямо сейчас
#   clinning-deploy status   версия на сервере и последние деплои
#
# Ход деплоя:
#   1. бэкап базы (pg_dump), git merge --ff-only origin/main
#   2. если менялись requirements.txt / Dockerfile / docker-compose*.yml,
#      образ пересобирается (старый контейнер работает, пока идёт сборка)
#   3. в отдельном контейнере на новом коде: manage.py check, migrate, collectstatic
#   4. переключение: обычно плавный перезапуск gunicorn (HUP) без простоя,
#      код примонтирован в контейнер; при пересборке — пересоздание контейнера
#      (несколько секунд простоя API; сайт этого не заметит)
#   5. проверка: /api/items/ отвечает 200 и JSON-массивом
#   При ошибке на любом шаге код возвращается на предыдущий коммит, а этот
#   коммит запоминается как неудачный и повторно не деплоится, пока не
#   появится новый.
set -euo pipefail

APP_DIR=/home/projects/clinning
BACKUP_DIR=/root/backups/clinning/auto
STATE_DIR=/var/lib/clinning-deploy
LOG=/var/log/clinning-deploy.log
KEEP_BACKUPS=20
HEALTH_URL=http://127.0.0.1:8111/api/items/

log() { echo "[$(date '+%F %T')] $*"; }
dc() { docker compose "$@"; }

healthy() {
  local i resp
  for i in $(seq 1 30); do
    resp=$(curl -s -m 5 -w '\n%{http_code}' "$HEALTH_URL" || true)
    if [ "${resp##*$'\n'}" = 200 ] && [ "${resp:0:1}" = "[" ]; then
      return 0
    fi
    sleep 2
  done
  return 1
}

deploy() {
  exec > >(tee -a "$LOG") 2>&1
  mkdir -p "$BACKUP_DIR" "$STATE_DIR"
  cd "$APP_DIR"

  local old new changed rebuild=no
  old=$(git rev-parse HEAD)
  git fetch -q origin main
  new=$(git rev-parse origin/main)
  if [ "$old" = "$new" ]; then
    log "Новых коммитов нет, на сервере уже $(git log --oneline -1)"
    return 0
  fi

  log "Деплой: $(git log --oneline -1 "$new") (было ${old:0:7})"

  fail() {
    log "ОШИБКА: $1"
    echo "$new" >"$STATE_DIR/failed_sha"
    if [ "$(git rev-parse HEAD)" != "$old" ]; then
      log "Возвращаю код на ${old:0:7}"
      git reset -q --hard "$old"
      if [ "$rebuild" = yes ]; then dc build -q web; fi
      dc up -d web >/dev/null 2>&1 || true
      dc restart web >/dev/null
      healthy && log "API снова работает на ${old:0:7}" || log "ВНИМАНИЕ: API не отвечает и после отката!"
    fi
    exit 1
  }

  local backup="$BACKUP_DIR/db-$(date +%F-%H%M%S)-${old:0:7}.sql.gz"
  dc exec -T db pg_dump -U clinning_user -d clinning | gzip >"$backup" ||
    fail "не удалось сделать бэкап базы"
  log "Бэкап базы: $backup"
  ls -1t "$BACKUP_DIR"/db-*.sql.gz | tail -n +$((KEEP_BACKUPS + 1)) | xargs -r rm -f

  git merge -q --ff-only origin/main ||
    fail "git merge --ff-only не прошёл (на сервере локальные правки или история разошлась)"

  changed=$(git diff --name-only "$old" "$new")
  if grep -qE '^(requirements\.txt|Dockerfile|docker-compose[^/]*\.ya?ml)$' <<<"$changed"; then
    rebuild=yes
    log "Изменились зависимости или Docker-конфигурация, пересобираю образ..."
    dc build -q web || fail "сборка образа не удалась"
  fi

  log "Проверка кода, миграции, статика..."
  dc run --rm --no-deps -T web sh -c \
    'python manage.py check && python manage.py migrate --noinput && python manage.py collectstatic --noinput -v 0' ||
    fail "check/migrate/collectstatic не прошли"

  if [ "$rebuild" = yes ]; then
    dc up -d web >/dev/null
    log "Контейнер пересоздан на новом образе"
  else
    dc kill -s HUP web >/dev/null
    log "gunicorn плавно перезапущен (HUP)"
  fi
  sleep 3

  healthy || fail "после переключения /api/items/ не отвечает"
  rm -f "$STATE_DIR/failed_sha"
  log "Готово: работает $(git log --oneline -1)"
}

check() {
  cd "$APP_DIR"
  git fetch -q origin main 2>/dev/null || exit 0
  local new
  new=$(git rev-parse origin/main)
  [ "$(git rev-parse HEAD)" = "$new" ] && exit 0
  # Неудачный коммит не пробуем каждую минуту: ждём следующего
  [ "$(cat "$STATE_DIR/failed_sha" 2>/dev/null)" = "$new" ] && exit 0
  deploy
}

status() {
  cd "$APP_DIR"
  git fetch -q origin main 2>/dev/null || true
  echo "На сервере: $(git log --oneline -1)"
  echo "В GitHub:   $(git log --oneline -1 origin/main)"
  if [ -f "$STATE_DIR/failed_sha" ]; then
    echo "Не удалось задеплоить: $(cat "$STATE_DIR/failed_sha" | cut -c1-7) (см. $LOG)"
  fi
  echo "Таймер автодеплоя: $(systemctl is-active clinning-deploy.timer 2>/dev/null || true)"
  echo "--- последние записи лога:"
  tail -6 "$LOG" 2>/dev/null || true
}

CMD="${1:-status}"
case "$CMD" in
check | deploy)
  exec 9>/run/lock/clinning-deploy.lock
  if [ "$CMD" = check ]; then
    flock -n 9 || exit 0 # деплой уже идёт
    check
  else
    flock -w 600 9 || { log "Другой деплой ещё идёт"; exit 1; }
    rm -f "$STATE_DIR/failed_sha"
    deploy
  fi
  ;;
status) status ;;
*)
  echo "Использование: clinning-deploy check | deploy | status"
  exit 2
  ;;
esac
