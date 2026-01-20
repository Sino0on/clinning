from django.db import models


class Item(models.Model):
    """Пример модели для демонстрации API"""
    key = models.CharField(max_length=200, verbose_name="Название", unique=True)
    value = models.TextField(blank=True, verbose_name="Описание")
    value_ru = models.TextField(blank=True, verbose_name="Описание на русском")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Элемент"
        verbose_name_plural = "Элементы"
        ordering = ["-created_at"]

    def __str__(self):
        return self.key
