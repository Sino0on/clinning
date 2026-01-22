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


class BackgroundImage(models.Model):
    image = models.FileField(blank=True, null=True, verbose_name='Задний фон')

    def __str__(self):
        return 'Задний фон'

    class Meta:
        verbose_name = 'Задний фон'
        verbose_name_plural = 'Задний фон'
    

class Partners(models.Model):
    logo = models.FileField(blank=True, null=True, verbose_name='Логотип')
    title = models.CharField(max_length=123, blank=True, null=True, verbose_name='Название')
    created_at = models.DateTimeField(verbose_name="Дата создания")
    

    def __str__(self):
        return f'{self.title}'

    class Meta:
        verbose_name = 'Партнер'
        verbose_name_plural = 'Партнеры'
        ordering = ['-created_at']


class Uslugi(models.Model):
    title = models.CharField(max_length=123, blank=True, null=True, verbose_name='Название')
    time = models.CharField(max_length=123, blank=True, null=True, verbose_name='Время')
    mini_description = models.CharField(max_length=123, blank=True, null=True, verbose_name='Краткое описание')
    image = models.FileField(blank=True, null=True, verbose_name='Изображение')
    created_at = models.DateTimeField(verbose_name="Дата создания")
    
    def __str__(self):
        return f'{self.title}'
    
    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
        ordering = ['-created_at']


class Doiposle(models.Model):
    title = models.CharField(max_length=123, blank=True, null=True, verbose_name='Название')
    time = models.CharField(max_length=123, blank=True, null=True, verbose_name='Время')
    mini_description = models.CharField(max_length=123, blank=True, null=True, verbose_name='Краткое описание')
    first_image = models.FileField(blank=True, null=True, verbose_name='Первое изображение')
    second_image = models.FileField(blank=True, null=True, verbose_name='Второе изображение')
    created_at = models.DateTimeField(verbose_name="Дата создания")
    
    def __str__(self):
        return f'{self.title}'
    
    class Meta:
        verbose_name = 'До и после'
        verbose_name_plural = 'До и после'
        ordering = ['-created_at']

countries = (
    ('Казахстан', 'Казахстан'),
    ('Россия', 'Россия'),
    ('Турция', 'Турция'),
    ('Узбекистан', 'Узбекистан'),
    ('Кыргызстан', 'Кыргызстан'),
    ('Казахстан', 'Казахстан'),
    ('Россия', 'Россия'),
    ('Турция', 'Турция'),
    ('Узбекистан', 'Узбекистан'),
    ('Кыргызстан', 'Кыргызстан'),
    ('Япония', 'Япония'),
    ('Китай', 'Китай'),
    ('Молдова', 'Молдова'),
    ('Грузия', 'Грузия'),
    ('Италия', 'Италия'),
    ('Германия', 'Германия'),
    ('Англия', 'Англия'),
    ('Франция', 'Франция'),
    ('Испания', 'Испания'),
    ('Германия', 'Германия'),
    ('Англия', 'Англия'),
    ('Франция', 'Франция'),
    ('Испания', 'Испания'),

)

class Useproduct(models.Model):
    title = models.CharField(max_length=123, blank=True, null=True, verbose_name='Название')
    time = models.CharField(max_length=123, blank=True, null=True, verbose_name='Время')
    country = models.CharField(max_length=123, choices=countries, blank=True, null=True, verbose_name='Страна')
    mini_description = models.CharField(max_length=123, blank=True, null=True, verbose_name='Краткое описание')
    image = models.FileField(blank=True, null=True, verbose_name='Изображение')
    created_at = models.DateTimeField(verbose_name="Дата создания")
    
    def __str__(self):
        return f'{self.title}'
    
    class Meta:
        verbose_name = 'Преимущества'
        verbose_name_plural = 'Преимущества'
        ordering = ['-created_at']


class Feedback(models.Model):
    file = models.FileField(blank=True, null=True, verbose_name='Файл')
    file_type = models.CharField(max_length=123, blank=True, null=True, verbose_name='Тип файла')
    created_at = models.DateTimeField(verbose_name="Дата создания")
    
    def __str__(self):
        return f'Отзыв {self.pk}'
    
    def save(self, *args, **kwargs):
        if self.file.name.split('.')[-1] in ['mp4', 'avi', 'mov', 'mkv']:
            self.file_type = 'video'
        else:
            self.file_type = 'image'
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

