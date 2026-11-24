# Автодеплой бэкенда

**Обычный случай: ничего делать не нужно.** Пуш в `main`, и в течение минуты
сервер сам подхватит изменения. Обычные правки кода выкатываются без простоя.

## Как это устроено

На сервере `217.114.0.30` systemd-таймер `clinning-deploy.timer` раз в минуту
запускает [deploy.sh](deploy.sh) (на сервере: `/usr/local/bin/clinning-deploy`).
Скрипт сравнивает версию на сервере с `origin/main` и при расхождении:

1. делает бэкап базы в `/root/backups/clinning/auto/` (хранятся последние 20);
2. подтягивает код (`git merge --ff-only`);
3. если менялись `requirements.txt`, `Dockerfile` или `docker-compose*.yml`,
   пересобирает образ;
4. в отдельном контейнере на новом коде выполняет `manage.py check`, `migrate`
   и `collectstatic`;
5. плавно перезапускает gunicorn (HUP, без простоя). При пересборке образа
   контейнер пересоздаётся, и API несколько секунд недоступен;
6. проверяет, что `/api/items/` отвечает.

Если любой шаг не прошёл, код возвращается на предыдущий коммит, а неудачный
коммит больше не пробуется, пока в `main` не появится новый.

Схема «сервер сам забирает» выбрана потому, что для GitHub Actions нужны
секреты репозитория, а их может добавлять только владелец (`Sino0on`).

## Команды на сервере

```bash
ssh root@217.114.0.30
clinning-deploy status   # версия на сервере и в GitHub, последние деплои
clinning-deploy deploy   # задеплоить прямо сейчас (в том числе повторить неудачный)
```

Лог: `/var/log/clinning-deploy.log`. Выключить автодеплой:
`systemctl disable --now clinning-deploy.timer`.

## Откат

Сделайте `git revert` проблемного коммита и запушьте: откат задеплоится так же.
Миграции базы назад автоматически не откатываются. Для этого есть бэкапы в
`/root/backups/clinning/auto/`.

## Если меняете файлы в этой папке

Сервер использует копии, их нужно обновить:

```bash
scp deploy/deploy.sh root@217.114.0.30:/usr/local/bin/clinning-deploy
scp deploy/clinning-deploy.service deploy/clinning-deploy.timer root@217.114.0.30:/etc/systemd/system/
ssh root@217.114.0.30 'systemctl daemon-reload'
```
