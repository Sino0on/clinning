"""Мгновенное обновление сайта после правок в админке.

После сохранения или удаления контента бэкенд дёргает
POST {FRONTEND_REVALIDATE_URL} с секретом, и Next.js сразу пересобирает
страницы. Без этого изменения появились бы в течение ~минуты (ISR).

Вызов отложенный (debounce 3 с): перетаскивание 20 карточек или импорт
Excel на 160 строк — это десятки сохранений, а запрос на сайт уйдёт один.
"""

import logging
import threading

import requests
from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_delete, post_save

logger = logging.getLogger(__name__)

DEBOUNCE_SECONDS = 3
_timer = None
_lock = threading.Lock()


def _send():
    try:
        r = requests.post(
            settings.FRONTEND_REVALIDATE_URL,
            headers={"x-revalidate-secret": settings.REVALIDATE_SECRET},
            timeout=15,
        )
        if r.status_code != 200:
            logger.warning("Обновление сайта: ответ %s %s", r.status_code, r.text[:200])
    except requests.RequestException as e:
        logger.warning("Обновление сайта не удалось: %s", e)


def _schedule():
    global _timer
    with _lock:
        if _timer is not None:
            _timer.cancel()
        _timer = threading.Timer(DEBOUNCE_SECONDS, _send)
        _timer.daemon = True
        _timer.start()


def revalidate_site(**kwargs):
    if not (settings.REVALIDATE_SECRET and settings.FRONTEND_REVALIDATE_URL):
        return
    transaction.on_commit(_schedule)


def connect():
    from api.models import Item

    from .models import BeforeAfter, ChemicalBrand, Partner, Review, Service

    for model in (Review, BeforeAfter, Service, Partner, ChemicalBrand, Item):
        post_save.connect(revalidate_site, sender=model, dispatch_uid=f"revalidate-save-{model.__name__}")
        post_delete.connect(revalidate_site, sender=model, dispatch_uid=f"revalidate-del-{model.__name__}")
