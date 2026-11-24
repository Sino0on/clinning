from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display

from .models import Item

# Разделы сайта по первой части ключа (hero.title → «Главный экран»)
SECTIONS = {
    "hero": "Главный экран",
    "about": "О нас",
    "nav": "Меню",
    "header": "Шапка",
    "brand": "Логотип",
    "services": "Услуги",
    "extra": "Доп. услуги",
    "advantages": "Преимущества",
    "partners": "Партнёры",
    "portfolio": "До и после",
    "video": "Видео",
    "reviews": "Отзывы",
    "chemicals": "Химия",
    "home": "Блок «Узнать цену»",
    "prices": "Страница цен",
    "subscription": "Абонементы",
    "calculator": "Калькулятор",
    "footer": "Подвал",
    "seo": "SEO главной",
    "seoPrices": "SEO страницы цен",
}


class SectionFilter(admin.SimpleListFilter):
    title = "Раздел сайта"
    parameter_name = "section"

    def lookups(self, request, model_admin):
        return list(SECTIONS.items())

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(key__startswith=f"{self.value()}.")
        return queryset


@admin.register(Item)
class ItemAdmin(ModelAdmin):
    list_display = ["section", "value", "value_ru", "key"]
    list_display_links = ["value"]
    list_filter = [SectionFilter]
    search_fields = ["value", "value_ru", "key"]
    ordering = ["key"]
    list_per_page = 50
    fields = ["key", "value", "value_ru"]

    @display(description="Раздел", label=True)
    def section(self, obj):
        return SECTIONS.get(obj.key.split(".", 1)[0], "Прочее")

    # Ключи технические: менять, добавлять и удалять их может только
    # администратор, иначе текст пропадёт с сайта.
    def get_readonly_fields(self, request, obj=None):
        return [] if request.user.is_superuser else ["key"]

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
