"""Админка контента. Делалась для человека, далёкого от IT:
понятные названия, превью картинок, сортировка перетаскиванием,
галочка «Показывать на сайте» прямо в списке."""

from django.contrib import admin, messages
from django.db import models
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin, StackedInline
from unfold.decorators import action, display
from unfold.widgets import UnfoldAdminCheckboxSelectMultipleWidget, UnfoldAdminTextareaWidget

from .models import (
    BeforeAfter,
    ChemicalBrand,
    Partner,
    Review,
    Service,
    ServicePage,
    ServicePageFAQ,
    TelegramEditor,
    TelegramInvite,
)
from .telegram import invite_link
from .video import start_video_processing


def _img(url, height=64, contain=False):
    if not url:
        return "—"
    fit = "contain" if contain else "cover"
    return format_html(
        '<img src="{}" alt="" loading="lazy" style="height:{}px;max-width:{}px;'
        'object-fit:{};border-radius:8px;background:#f3f4f6">',
        url,
        height,
        height * 2,
        fit,
    )


def _large(url, contain=False):
    if not url:
        return "—"
    fit = "contain" if contain else "cover"
    return format_html(
        '<img src="{}" alt="" style="max-height:360px;max-width:100%;'
        'object-fit:{};border-radius:12px">',
        url,
        fit,
    )


class ContentAdmin(ModelAdmin):
    """Общее: перетаскивание для порядка, публикация прямо в списке."""

    ordering_field = "position"
    hide_ordering_field = True
    list_editable = ["is_published"]
    list_filter = ["is_published"]
    list_per_page = 50
    warn_unsaved_form = True

    # Пока запись не создана, превью «Сейчас загружено» и служебные поля
    # пустые — на форме добавления их не показываем.
    add_hidden_fields = ("preview_large", "preview_pair", "status_badge", "error")

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj is not None:
            return fieldsets
        cleaned = []
        for name, opts in fieldsets:
            fields = [f for f in opts["fields"] if f not in self.add_hidden_fields]
            if fields:
                cleaned.append((name, {**opts, "fields": fields}))
        return cleaned


@admin.register(Review)
class ReviewAdmin(ContentAdmin):
    list_display = ["preview", "kind_badge", "caption_ru", "status_badge", "is_published"]
    list_filter = ["is_published", "kind"]
    readonly_fields = ["preview_large", "status_badge", "error"]
    fieldsets = (
        (None, {"fields": ("file", "preview_large")}),
        ("Подпись", {"fields": ("caption_ru", "caption_ky")}),
        ("Публикация", {"fields": ("is_published",)}),
        ("Обработка видео", {"fields": ("status_badge", "error"), "classes": ["collapse"]}),
    )
    actions = ["reprocess"]

    @display(description="Превью")
    def preview(self, obj):
        if obj.kind == Review.Kind.VIDEO:
            return _img(obj.poster.url if obj.poster else None)
        return _img(obj.file.url if obj.file else None)

    @display(description="Сейчас загружено")
    def preview_large(self, obj):
        if not obj.pk or not obj.file:
            return "—"
        if obj.kind == Review.Kind.VIDEO:
            if obj.status != Review.Status.READY:
                return "Видео обрабатывается, превью появится через 1–3 минуты (обновите страницу)."
            return format_html(
                '<video src="{}" poster="{}" controls preload="none" '
                'style="max-height:360px;border-radius:12px"></video>',
                obj.file.url,
                obj.poster.url if obj.poster else "",
            )
        return _large(obj.file.url)

    @display(description="Тип", label={"Фото": "info", "Видео": "primary"})
    def kind_badge(self, obj):
        return obj.get_kind_display()

    @display(
        description="Статус",
        label={
            "Готово": "success",
            "Видео обрабатывается": "warning",
            "Ошибка обработки": "danger",
        },
    )
    def status_badge(self, obj):
        return obj.get_status_display()

    @action(description="Обработать видео заново")
    def reprocess(self, request, queryset):
        videos = queryset.filter(kind=Review.Kind.VIDEO)
        for review in videos:
            review.status = Review.Status.PROCESSING
            review.error = ""
            review.save(update_fields=["status", "error", "updated_at"])
            start_video_processing(review.pk)
        self.message_user(
            request,
            f"Запущена обработка видео: {videos.count()}. Это займёт 1–3 минуты.",
            messages.SUCCESS,
        )


@admin.register(BeforeAfter)
class BeforeAfterAdmin(ContentAdmin):
    list_display = ["preview_before", "preview_after", "title_ru", "is_published"]
    readonly_fields = ["preview_pair"]
    fieldsets = (
        ("Фото", {"fields": ("before", "after", "preview_pair")}),
        ("Русский", {"fields": ("title_ru", "description_ru")}),
        ("Кыргызча", {"fields": ("title_ky", "description_ky")}),
        ("Публикация", {"fields": ("is_published",)}),
    )

    @display(description="До")
    def preview_before(self, obj):
        return _img(obj.before.url if obj.before else None)

    @display(description="После")
    def preview_after(self, obj):
        return _img(obj.after.url if obj.after else None)

    @display(description="Сейчас загружено")
    def preview_pair(self, obj):
        if not obj.pk:
            return "—"
        return format_html(
            '<div style="display:flex;gap:12px;flex-wrap:wrap">{}{}</div>',
            _large(obj.before.url if obj.before else None),
            _large(obj.after.url if obj.after else None),
        )


@admin.register(Service)
class ServiceAdmin(ContentAdmin):
    list_display = ["preview", "title_ru", "duration_ru", "is_published"]
    readonly_fields = ["preview_large"]
    fieldsets = (
        ("Фото", {"fields": ("image", "preview_large")}),
        ("Русский", {"fields": ("title_ru", "duration_ru", "description_ru")}),
        ("Кыргызча", {"fields": ("title_ky", "duration_ky", "description_ky")}),
        ("Публикация", {"fields": ("is_published",)}),
    )

    @display(description="Фото")
    def preview(self, obj):
        return _img(obj.image.url if obj.image else None)

    @display(description="Сейчас загружено")
    def preview_large(self, obj):
        return _large(obj.image.url if obj.image else None)


class ServicePageFAQInline(StackedInline):
    model = ServicePageFAQ
    extra = 0
    ordering_field = "position"
    hide_ordering_field = True
    fields = ["question_ru", "answer_ru", "question_ky", "answer_ky", "position"]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if isinstance(db_field, models.TextField):
            kwargs["widget"] = _lines_widget(3)
        return super().formfield_for_dbfield(db_field, request, **kwargs)


def _lines_widget(rows):
    return UnfoldAdminTextareaWidget(attrs={"rows": rows})


@admin.register(ServicePage)
class ServicePageAdmin(ContentAdmin):
    """Отдельные страницы услуг. Новую проще всего сделать копией готовой:
    кнопка «Создать копию» сверху формы или в строке списка."""

    list_display = ["preview", "name_ru", "page_link", "is_published"]
    # Иначе ссылкой на форму был бы только прочерк, пока нет фото
    list_display_links = ["preview", "name_ru"]
    readonly_fields = ["preview_large", "page_links"]
    inlines = [ServicePageFAQInline]
    add_hidden_fields = ContentAdmin.add_hidden_fields + ("page_links",)
    fieldsets = (
        (
            "Русский",
            {
                "classes": ["tab"],
                "fields": (
                    "name_ru",
                    "title_ru",
                    "lead_ru",
                    ("price_ru", "duration_ru"),
                    "includes_ru",
                    "body_ru",
                ),
            },
        ),
        (
            "Кыргызча",
            {
                "classes": ["tab"],
                "description": "Если поле не заполнено, на кыргызской версии страницы будет русский текст.",
                "fields": (
                    "name_ky",
                    "title_ky",
                    "lead_ky",
                    ("price_ky", "duration_ky"),
                    "includes_ky",
                    "body_ky",
                ),
            },
        ),
        (
            "Фото и примеры",
            {"classes": ["tab"], "fields": ("image", "preview_large", "before_after")},
        ),
        (
            "Для Google",
            {
                "classes": ["tab"],
                "description": "Необязательно: если пусто, Google покажет заголовок и подзаголовок страницы.",
                "fields": (
                    "seo_title_ru",
                    "seo_description_ru",
                    "seo_title_ky",
                    "seo_description_ky",
                ),
            },
        ),
        (
            "Публикация",
            {
                "classes": ["tab"],
                "fields": ("is_published", "page_links", "slug", "service"),
            },
        ),
    )
    actions_detail = ["open_on_site", "make_copy"]
    actions_row = ["make_copy_row"]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        rows = {"includes_ru": 8, "includes_ky": 8, "body_ru": 12, "body_ky": 12, "lead_ru": 3, "lead_ky": 3}
        if db_field.name in rows:
            kwargs["widget"] = _lines_widget(rows[db_field.name])
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # Галочки вместо списка с множественным выбором (удобно с телефона).
        # Виджет передаём сразу, иначе Django допишет к подсказке «Удерживайте Ctrl…»,
        # а стили возвращаем после super(): Unfold навешивает стили выпадающего списка.
        if db_field.name == "before_after":
            kwargs["widget"] = UnfoldAdminCheckboxSelectMultipleWidget()
        field = super().formfield_for_manytomany(db_field, request, **kwargs)
        if field is not None and db_field.name == "before_after":
            field.widget.attrs = UnfoldAdminCheckboxSelectMultipleWidget().attrs
        return field

    @display(description="Фото")
    def preview(self, obj):
        return _img(obj.image.url if obj.image else None)

    @display(description="Сейчас загружено")
    def preview_large(self, obj):
        return _large(obj.image.url if obj.image else None)

    @display(description="Адрес на сайте")
    def page_link(self, obj):
        url = ServicePage.site_url(obj.slug)
        return format_html('<a href="{0}" target="_blank" rel="noopener">/uslugi/{1}</a>', url, obj.slug)

    @display(description="Страница на сайте")
    def page_links(self, obj):
        if not obj.pk:
            return "Появится после сохранения"
        hint = "" if obj.is_published else " (сейчас скрыта: откроется после включения «Показывать на сайте»)"
        return format_html(
            '<a href="{0}" target="_blank" rel="noopener">{0}</a><br>'
            '<a href="{1}" target="_blank" rel="noopener">{1}</a>{2}',
            ServicePage.site_url(obj.slug, "ru"),
            ServicePage.site_url(obj.slug, "ky"),
            hint,
        )

    def _copy(self, request, object_id):
        page = ServicePage.objects.get(pk=object_id)
        copy = page.duplicate()
        self.message_user(
            request,
            "Создана копия страницы (пока скрыта с сайта). Перепишите русские тексты "
            "под новую услугу, поменяйте фото и адрес. Кыргызские тексты и тексты для "
            "Google в копии пустые: заполните их или оставьте пустыми, тогда возьмутся "
            "русские. Затем включите «Показывать на сайте» на вкладке «Публикация».",
            messages.SUCCESS,
        )
        return redirect(reverse("admin:content_servicepage_change", args=[copy.pk]))

    def has_copy_permission(self, request, object_id=None):
        # Своя проверка: Unfold передаёт сюда ещё и object_id, а has_add_permission его не принимает
        return self.has_add_permission(request)

    @action(description="Создать копию", icon="content_copy", permissions=["copy"])
    def make_copy(self, request, object_id):
        return self._copy(request, object_id)

    @action(description="Создать копию", icon="content_copy", permissions=["copy"])
    def make_copy_row(self, request, object_id):
        return self._copy(request, object_id)

    @action(description="Открыть на сайте", icon="open_in_new", attrs={"target": "_blank"})
    def open_on_site(self, request, object_id):
        page = ServicePage.objects.get(pk=object_id)
        if not page.is_published:
            self.message_user(
                request,
                "Страница скрыта. Включите «Показывать на сайте» на вкладке «Публикация» и сохраните.",
                messages.WARNING,
            )
            return redirect(reverse("admin:content_servicepage_change", args=[page.pk]))
        return redirect(ServicePage.site_url(page.slug))


@admin.register(Partner)
class PartnerAdmin(ContentAdmin):
    list_display = ["preview", "name", "link", "is_published"]
    readonly_fields = ["preview_large"]
    fields = ["name", "logo", "preview_large", "link", "is_published"]

    @display(description="Логотип")
    def preview(self, obj):
        return _img(obj.logo.url if obj.logo else None, contain=True)

    @display(description="Сейчас загружено")
    def preview_large(self, obj):
        return _large(obj.logo.url if obj.logo else None, contain=True)


@admin.register(ChemicalBrand)
class ChemicalBrandAdmin(ContentAdmin):
    list_display = ["preview", "name", "country", "is_published"]
    readonly_fields = ["preview_large"]
    fieldsets = (
        (None, {"fields": ("name", "country", "logo", "preview_large")}),
        ("Описание", {"fields": ("description_ru", "description_ky")}),
        ("Публикация", {"fields": ("is_published",)}),
    )

    @display(description="Логотип")
    def preview(self, obj):
        return _img(obj.logo.url if obj.logo else None, contain=True)

    @display(description="Сейчас загружено")
    def preview_large(self, obj):
        return _large(obj.logo.url if obj.logo else None, contain=True)


# ---------- Telegram-бот (только для администратора) ----------


@admin.register(TelegramInvite)
class TelegramInviteAdmin(ModelAdmin):
    """Ссылки-приглашения: создайте запись, отправьте ссылку человеку."""

    list_display = ["note", "link", "used_by", "used_at", "created_at"]
    readonly_fields = ["link", "used_by", "used_at"]
    fields = ["note", "link", "used_by", "used_at"]

    @display(description="Ссылка-приглашение")
    def link(self, obj):
        if not obj.pk:
            return "Появится после сохранения"
        if obj.used_at:
            return "Уже использована"
        url = invite_link(obj.code)
        if not url:
            return "Бот не настроен: нет TELEGRAM_BOT_TOKEN"
        return format_html('<a href="{0}" target="_blank" rel="noopener">{0}</a>', url)

    def has_module_permission(self, request):
        return request.user.is_superuser


@admin.register(TelegramEditor)
class TelegramEditorAdmin(ModelAdmin):
    """Кто может публиковать отзывы через бота. Снимите «Доступ разрешён», чтобы закрыть."""

    list_display = ["name", "telegram_id", "is_active", "created_at"]
    list_editable = ["is_active"]
    readonly_fields = ["telegram_id", "created_at"]
    fields = ["name", "telegram_id", "is_active", "created_at"]

    def has_add_permission(self, request):
        return False  # редакторы появляются только по приглашению

    def has_module_permission(self, request):
        return request.user.is_superuser
