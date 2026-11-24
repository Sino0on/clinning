from django.db import models


class Item(models.Model):
    """Текст сайта по ключу (например, hero.title) на двух языках.

    Исторически поле value_ru хранит КЫРГЫЗСКИЙ текст: так его читает сайт.
    Переименовывать не стали, чтобы не ломать импорт из Excel и API.
    Отзывы, «до/после», партнёры, услуги и бренды — в приложении content.
    """

    key = models.CharField(
        max_length=200,
        verbose_name="Ключ",
        unique=True,
        help_text="Технический адрес текста на сайте. Не меняйте.",
    )
    value = models.TextField(blank=True, verbose_name="Текст — русский")
    value_ru = models.TextField(blank=True, verbose_name="Текст — кыргызча")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Текст сайта"
        verbose_name_plural = "Тексты сайта"
        ordering = ["-created_at"]

    def __str__(self):
        return self.key
