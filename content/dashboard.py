"""Данные для стартовой страницы админки (UNFOLD["DASHBOARD_CALLBACK"])."""

from django.urls import reverse

from api.models import Item

from .models import BeforeAfter, ChemicalBrand, Partner, Review, Service, ServicePage

SITE_URL = "https://taza-ayim.kg/ru"

# (модель, что добавить, иконка Material Symbols, подсказка)
ADD_ACTIONS = [
    (Review, "Отзыв", "add_photo_alternate", "Фото, скриншот или видео с телефона"),
    (BeforeAfter, "До и после", "compare", "Два фото одной уборки"),
    (Service, "Услугу", "cleaning_services", "Название, время, описание, фото"),
    (ServicePage, "Страницу услуги", "article", "Своя страница для Google. Проще сделать копией готовой"),
    (Partner, "Партнёра", "handshake", "Логотип и ссылка"),
]

SECTIONS = [
    (Review, "Отзывы", "reviews"),
    (BeforeAfter, "До и после", "compare"),
    (Service, "Услуги", "cleaning_services"),
    (ServicePage, "Страницы услуг", "article"),
    (Partner, "Партнёры", "handshake"),
    (ChemicalBrand, "Бренды химии", "science"),
]


def _perm(user, model, action):
    return user.has_perm(f"{model._meta.app_label}.{action}_{model._meta.model_name}")


def dashboard_callback(request, context):
    user = request.user
    opts = lambda m: (m._meta.app_label, m._meta.model_name)  # noqa: E731

    add_actions = [
        {
            "title": title,
            "icon": icon,
            "hint": hint,
            "url": reverse("admin:%s_%s_add" % opts(model)),
        }
        for model, title, icon, hint in ADD_ACTIONS
        if _perm(user, model, "add")
    ]

    sections = []
    for model, title, icon in SECTIONS:
        if not _perm(user, model, "view"):
            continue
        qs = model.objects.all()
        published = qs.filter(is_published=True)
        if model is Review:
            published = published.filter(status=Review.Status.READY)
        sections.append(
            {
                "title": title,
                "icon": icon,
                "published": published.count(),
                "hidden": qs.filter(is_published=False).count(),
                "url": reverse("admin:%s_%s_changelist" % opts(model)),
            }
        )
    if user.has_perm("api.view_item"):
        sections.append(
            {
                "title": "Тексты сайта",
                "icon": "translate",
                "published": Item.objects.count(),
                "hidden": 0,
                "url": reverse("admin:api_item_changelist"),
                "texts": True,
            }
        )

    videos = Review.objects.filter(kind=Review.Kind.VIDEO)
    context.update(
        {
            "dashboard": {
                "add_actions": add_actions,
                "sections": sections,
                "videos_processing": videos.filter(status=Review.Status.PROCESSING).count(),
                "videos_failed": videos.filter(status=Review.Status.FAILED).count(),
                "reviews_url": reverse("admin:content_review_changelist"),
                "site_url": SITE_URL,
                "site_attrs": {"target": "_blank", "rel": "noopener"},
            }
        }
    )
    return context
