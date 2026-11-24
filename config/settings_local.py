# Локальная разработка без Docker/Postgres: SQLite и файлы в папке проекта.
# Запуск: set DJANGO_SETTINGS_MODULE=config.settings_local (в .venv)
import os

os.environ.setdefault("SECRET_KEY", "local-dev-only-not-secret")
for _k in ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST"):
    os.environ.setdefault(_k, "unused")
os.environ.setdefault("POSTGRES_PORT", "5432")

from .settings import *  # noqa: E402,F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "local.sqlite3",  # noqa: F405
    }
}
PUBLIC_BASE_URL = "http://127.0.0.1:8111"
REVALIDATE_SECRET = ""
