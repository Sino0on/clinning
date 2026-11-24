"""Мгновенное обновление сайта после правок в админке.

После сохранения или удаления контента бэкенд дёргает
POST {FRONTEND_REVALIDATE_URL} с секретом, и Next.js сразу пересобирает
страницы. Без этого изменения появились бы в течение ~минуты (ISR).

Вызов отложенный (debounce 3 с): перетаскивание 20 карточек или импорт
Excel на 160 строк — это десятки сохранений, а запрос на сайт уйдёт один.
"""

import logging
import threading
import time
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_delete, post_save

logger = logging.getLogger(__name__)

DEBOUNCE_SECONDS = 3
# Страницы сайта, которые используют контент из админки
# (плюс опубликованные страницы услуг, см. _warmup_paths)
WARMUP_PATHS = ["/ru", "/ky", "/ru/prices", "/ky/prices"]
_timer = None
_lock = threading.Lock()


def _send(warmup_paths):
    try:
        r = requests.post(
            settings.FRONTEND_REVALIDATE_URL,
            headers={"x-revalidate-secret": settings.REVALIDATE_SECRET},
            timeout=15,
        )
        if r.status_code != 200:
            logger.warning("Обновление сайта: ответ %s %s", r.status_code, r.text[:200])
            return
        # Прогрев: сайт сбрасывает кэш в режиме stale-while-revalidate, и
        # первый запрос после сброса получает прежнюю версию, запуская
        # пересборку в фоне. Этот запрос делаем сами, чтобы посетители
        # (и сама заказчица, проверяя правку) сразу видели новое.
        time.sleep(1)
        for path in warmup_paths:
            requests.get(urljoin(settings.FRONTEND_REVALIDATE_URL, path), timeout=30)
    except requests.RequestException as e:
        logger.warning("Обновление сайта не удалось: %s", e)


def _warmup_paths():
    # Считаем здесь, в потоке запроса: в фоновом потоке Django открыл бы
    # к базе новое соединение и не закрыл бы его.
    from .models import ServicePage

    slugs = ServicePage.objects.filter(is_published=True).values_list("slug", flat=True)
    return WARMUP_PATHS + [f"/{lang}/uslugi/{slug}" for slug in slugs for lang in ("ru", "ky")]


def _schedule():
    global _timer
    with _lock:
        if _timer is not None:
            _timer.cancel()
        _timer = threading.Timer(DEBOUNCE_SECONDS, _send, args=(_warmup_paths(),))
        _timer.daemon = True
        _timer.start()


def revalidate_site(**kwargs):
    if not (settings.REVALIDATE_SECRET and settings.FRONTEND_REVALIDATE_URL):
        return
    transaction.on_commit(_schedule)


def connect():
    from api.models import Item

    from .models import (
        BeforeAfter,
        ChemicalBrand,
        Partner,
        Review,
        Service,
        ServicePage,
        ServicePageFAQ,
    )

    models = (Review, BeforeAfter, Service, ServicePage, ServicePageFAQ, Partner, ChemicalBrand, Item)
    for model in models:
        post_save.connect(revalidate_site, sender=model, dispatch_uid=f"revalidate-save-{model.__name__}")
        post_delete.connect(revalidate_site, sender=model, dispatch_uid=f"revalidate-del-{model.__name__}")
