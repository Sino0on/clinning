"""Контент сайта taza-ayim.kg, который заказчица редактирует сама в админке.

Тексты на двух языках: *_ru — русский, *_ky — кыргызский.
Картинки при загрузке автоматически поворачиваются по EXIF, уменьшаются
и пережимаются; видео-отзывы сжимаются в фоне (см. video.py).
"""

import secrets

from django.db import models, transaction
from django.utils.text import slugify

from .media import (
    image_validators,
    optimize_image,
    review_file_validators,
    VIDEO_EXTENSIONS,
)


class SortablePublishable(models.Model):
    is_published = models.BooleanField("Показывать на сайте", default=True)
    position = models.IntegerField("Порядок", default=0, db_index=True)
    created_at = models.DateTimeField("Добавлено", auto_now_add=True)
    updated_at = models.DateTimeField("Изменено", auto_now=True)

    class Meta:
        abstract = True
        ordering = ["position", "-created_at"]

    def save(self, *args, **kwargs):
        # Новая запись встаёт первой в списке (её потом можно перетащить)
        if self._state.adding and not self.position:
            first = (
                type(self)
                .objects.order_by("position")
                .values_list("position", flat=True)
                .first()
            )
            self.position = first - 1 if first is not None else 0
        super().save(*args, **kwargs)


class Review(SortablePublishable):
    class Kind(models.TextChoices):
        PHOTO = "photo", "Фото"
        VIDEO = "video", "Видео"

    class Status(models.TextChoices):
        READY = "ready", "Готово"
        PROCESSING = "processing", "Видео обрабатывается"
        FAILED = "failed", "Ошибка обработки"

    file = models.FileField(
        "Фото или видео",
        upload_to="reviews/%Y/%m/",
        validators=review_file_validators(),
        help_text=(
            "Фото или скриншот (JPG, PNG, WEBP) либо видео (MP4, MOV) до 300 МБ. "
            "Видео само сожмётся для сайта за 1–3 минуты, обложка сделается автоматически."
        ),
    )
    poster = models.ImageField(
        "Обложка видео", upload_to="reviews/%Y/%m/", blank=True, editable=False
    )
    kind = models.CharField(
        "Тип", max_length=10, choices=Kind.choices, default=Kind.PHOTO, editable=False
    )
    status = models.CharField(
        "Статус",
        max_length=12,
        choices=Status.choices,
        default=Status.READY,
        editable=False,
    )
    error = models.TextField("Текст ошибки", blank=True, editable=False)
    caption_ru = models.CharField(
        "Подпись (русский)",
        max_length=200,
        blank=True,
        help_text="Необязательно. Например: «Отзыв Айгуль, генеральная уборка».",
    )
    caption_ky = models.CharField("Подпись (кыргызча)", max_length=200, blank=True)
    # Если отзыв пришёл через Telegram-бота: куда написать, когда видео готово
    telegram_chat_id = models.BigIntegerField(null=True, blank=True, editable=False)

    # Импорт уже готовых (сжатых) видео без повторной обработки
    skip_processing = False

    class Meta(SortablePublishable.Meta):
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

    def __str__(self):
        return self.caption_ru or f"Отзыв №{self.pk}"

    def save(self, *args, **kwargs):
        new_upload = bool(self.file) and not self.file._committed
        start_processing = False
        if new_upload:
            ext = self.file.name.rsplit(".", 1)[-1].lower()
            if ext in VIDEO_EXTENSIONS:
                self.kind = self.Kind.VIDEO
                if not self.skip_processing:
                    self.status = self.Status.PROCESSING
                    self.error = ""
                    start_processing = True
            else:
                self.kind = self.Kind.PHOTO
                self.status = self.Status.READY
                self.poster = None
                optimize_image(self.file, max_side=1600)
        super().save(*args, **kwargs)
        if start_processing:
            from .video import start_video_processing

            pk = self.pk
            transaction.on_commit(lambda: start_video_processing(pk))


class BeforeAfter(SortablePublishable):
    title_ru = models.CharField("Название (русский)", max_length=120)
    title_ky = models.CharField("Название (кыргызча)", max_length=120, blank=True)
    description_ru = models.CharField(
        "Описание (русский)", max_length=300, blank=True
    )
    description_ky = models.CharField(
        "Описание (кыргызча)", max_length=300, blank=True
    )
    before = models.ImageField(
        "Фото «до»",
        upload_to="before-after/%Y/%m/",
        validators=image_validators(),
        help_text="Лучше вертикальное фото, снятое с той же точки, что и «после».",
    )
    after = models.ImageField(
        "Фото «после»", upload_to="before-after/%Y/%m/", validators=image_validators()
    )

    class Meta(SortablePublishable.Meta):
        verbose_name = "До и после"
        verbose_name_plural = "До и после"

    def __str__(self):
        return self.title_ru

    def save(self, *args, **kwargs):
        optimize_image(self.before, max_side=1600)
        optimize_image(self.after, max_side=1600)
        super().save(*args, **kwargs)


class Service(SortablePublishable):
    title_ru = models.CharField("Название (русский)", max_length=120)
    title_ky = models.CharField("Название (кыргызча)", max_length=120, blank=True)
    duration_ru = models.CharField(
        "Время работы (русский)", max_length=60, blank=True, help_text="Например: 6–8 часов"
    )
    duration_ky = models.CharField(
        "Время работы (кыргызча)", max_length=60, blank=True, help_text="Мисалы: 6–8 саат"
    )
    description_ru = models.TextField("Описание (русский)", blank=True)
    description_ky = models.TextField("Описание (кыргызча)", blank=True)
    image = models.ImageField(
        "Фото",
        upload_to="services/%Y/%m/",
        blank=True,
        validators=image_validators(),
        help_text="Лучше своё фото с реальной уборки. Если фото нет, на сайте временная картинка.",
    )

    class Meta(SortablePublishable.Meta):
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"

    def __str__(self):
        return self.title_ru

    def save(self, *args, **kwargs):
        optimize_image(self.image, max_side=1200)
        super().save(*args, **kwargs)


# ---------- Страницы услуг: taza-ayim.kg/ru/uslugi/<slug> ----------

# Латиница для адреса страницы (русские и кыргызские буквы)
_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "ң": "n",
    "о": "o", "ө": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ү": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y",
    "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def slug_from_text(text):
    """«Уборка после стройки» → «uborka-posle-stroyki»."""
    latin = "".join(_TRANSLIT.get(ch, ch) for ch in text.lower())
    return slugify(latin)[:70].strip("-") or "usluga"


class ServicePage(SortablePublishable):
    """Отдельная страница одной услуги для Google: taza-ayim.kg/ru/uslugi/<slug>.

    Пустые кыргызские поля на сайте заменяются русскими. Пустые разделы
    (например, «Что входит» или вопросы) на странице просто не выводятся.
    """

    slug = models.SlugField(
        "Адрес страницы",
        max_length=80,
        unique=True,
        blank=True,
        help_text=(
            "Латинскими буквами через дефис, например uborka-posle-stroyki. "
            "Если оставить пустым, адрес составится из короткого названия. "
            "После публикации лучше не менять: старые ссылки перестанут работать."
        ),
    )
    name_ru = models.CharField(
        "Короткое название (русский)",
        max_length=80,
        help_text="Для ссылок и кнопок, например: «Уборка после стройки».",
    )
    name_ky = models.CharField("Короткое название (кыргызча)", max_length=80, blank=True)
    title_ru = models.CharField(
        "Заголовок страницы (русский)",
        max_length=120,
        help_text="Самый крупный текст на странице. Хорошо, если в нём есть город: «Уборка после стройки в Бишкеке».",
    )
    title_ky = models.CharField("Заголовок страницы (кыргызча)", max_length=120, blank=True)
    lead_ru = models.TextField(
        "Подзаголовок (русский)",
        max_length=400,
        help_text="1–2 предложения под заголовком: что вы сделаете для клиента.",
    )
    lead_ky = models.TextField("Подзаголовок (кыргызча)", max_length=400, blank=True)
    price_ru = models.CharField(
        "Цена (русский)", max_length=60, blank=True, help_text="Например: от 110 сом за м²"
    )
    price_ky = models.CharField(
        "Цена (кыргызча)", max_length=60, blank=True, help_text="Мисалы: м² үчүн 110 сомдон"
    )
    duration_ru = models.CharField(
        "Время работы (русский)", max_length=60, blank=True, help_text="Например: 12–24 часа"
    )
    duration_ky = models.CharField(
        "Время работы (кыргызча)", max_length=60, blank=True, help_text="Мисалы: 12–24 саат"
    )
    includes_ru = models.TextField(
        "Что входит (русский)",
        blank=True,
        help_text="Каждый пункт с новой строки. На сайте это будет список с галочками.",
    )
    includes_ky = models.TextField("Что входит (кыргызча)", blank=True)
    body_ru = models.TextField(
        "Подробный текст (русский)",
        blank=True,
        help_text=(
            "Несколько абзацев об услуге своими словами. Абзацы разделяйте пустой строкой. "
            "Такой текст помогает странице подняться в Google."
        ),
    )
    body_ky = models.TextField("Подробный текст (кыргызча)", blank=True)
    image = models.ImageField(
        "Главное фото",
        upload_to="service-pages/%Y/%m/",
        blank=True,
        validators=image_validators(),
        help_text="Своё фото с такой уборки, лучше горизонтальное. Можно без фото.",
    )
    before_after = models.ManyToManyField(
        BeforeAfter,
        verbose_name="Примеры работ «до и после»",
        blank=True,
        help_text="Отметьте работы из раздела «До и после», которые подходят к этой услуге.",
    )
    service = models.OneToOneField(
        Service,
        verbose_name="Карточка на главной",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="page",
        help_text="У этой карточки в «Выберите вид уборки» на главной появится кнопка «Подробнее».",
    )
    seo_title_ru = models.CharField(
        "Заголовок в Google (русский)",
        max_length=80,
        blank=True,
        help_text="Синяя ссылка в поиске, до 60 знаков. Если пусто, возьмётся заголовок страницы.",
    )
    seo_title_ky = models.CharField("Заголовок в Google (кыргызча)", max_length=80, blank=True)
    seo_description_ru = models.CharField(
        "Описание в Google (русский)",
        max_length=200,
        blank=True,
        help_text="Текст под ссылкой в поиске, до 160 знаков. Если пусто, возьмётся подзаголовок.",
    )
    seo_description_ky = models.CharField("Описание в Google (кыргызча)", max_length=200, blank=True)

    class Meta(SortablePublishable.Meta):
        verbose_name = "Страница услуги"
        verbose_name_plural = "Страницы услуг"

    def __str__(self):
        return self.name_ru

    @staticmethod
    def site_url(slug, lang="ru"):
        return f"https://taza-ayim.kg/{lang}/uslugi/{slug}"

    def _unique_slug(self, base):
        slug, n = base, 2
        while ServicePage.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base}-{n}"
            n += 1
        return slug

    def save(self, *args, **kwargs):
        self.slug = self._unique_slug((self.slug or "").strip().lower() or slug_from_text(self.name_ru))
        optimize_image(self.image, max_side=1600)
        super().save(*args, **kwargs)

    # Что очищается в копии: если заказчица перепишет только русский текст,
    # кыргызская версия и сниппет в Google не должны рассказывать о старой
    # услуге. Пустые поля на сайте заменяются русским текстом и заголовком.
    COPY_CLEARED_FIELDS = (
        "name_ky", "title_ky", "lead_ky", "price_ky", "duration_ky", "includes_ky", "body_ky",
        "seo_title_ru", "seo_title_ky", "seo_description_ru", "seo_description_ky",
    )

    @transaction.atomic
    def duplicate(self):
        """Копия страницы с русскими текстами, фото и вопросами — заготовка
        для новой услуги. Копия скрыта с сайта, пока её не отредактируют."""
        faq = list(self.faq.all())
        examples = list(self.before_after.all())
        copy = ServicePage.objects.get(pk=self.pk)
        copy.pk = copy.id = None
        copy._state.adding = True
        copy.position = 0
        copy.is_published = False
        copy.service = None
        copy.name_ru = f"{self.name_ru} (копия)"[:80]
        copy.slug = f"{self.slug}-kopiya"
        for field in self.COPY_CLEARED_FIELDS:
            setattr(copy, field, "")
        copy.save()
        copy.before_after.set(examples)
        for item in faq:
            item.pk = None
            item.page = copy
            item.question_ky = item.answer_ky = ""
            item.save()
        return copy


class ServicePageFAQ(models.Model):
    page = models.ForeignKey(ServicePage, on_delete=models.CASCADE, related_name="faq")
    question_ru = models.CharField("Вопрос (русский)", max_length=200)
    answer_ru = models.TextField("Ответ (русский)")
    question_ky = models.CharField("Вопрос (кыргызча)", max_length=200, blank=True)
    answer_ky = models.TextField("Ответ (кыргызча)", blank=True)
    position = models.IntegerField("Порядок", default=0, db_index=True)

    class Meta:
        verbose_name = "Вопрос и ответ"
        verbose_name_plural = "Вопросы и ответы"
        ordering = ["position", "id"]

    def __str__(self):
        return self.question_ru


class Partner(SortablePublishable):
    name = models.CharField("Название", max_length=120)
    logo = models.ImageField(
        "Логотип", upload_to="partners/", validators=image_validators()
    )
    link = models.URLField(
        "Ссылка", blank=True, help_text="Сайт или Instagram партнёра (необязательно)."
    )

    class Meta(SortablePublishable.Meta):
        verbose_name = "Партнёр"
        verbose_name_plural = "Партнёры"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        optimize_image(self.logo, max_side=600)
        super().save(*args, **kwargs)


class ChemicalBrand(SortablePublishable):
    class Country(models.TextChoices):
        GERMANY = "Germany", "Германия"
        RUSSIA = "Russia", "Россия"
        TURKEY = "Turkey", "Турция"
        KYRGYZSTAN = "Kyrgyzstan", "Кыргызстан"
        KAZAKHSTAN = "Kazakhstan", "Казахстан"
        CHINA = "China", "Китай"
        ITALY = "Italy", "Италия"
        OTHER = "Other", "Другая"

    # Названия стран по-кыргызски для сайта
    COUNTRY_KY = {
        "Germany": "Германия",
        "Russia": "Россия",
        "Turkey": "Түркия",
        "Kyrgyzstan": "Кыргызстан",
        "Kazakhstan": "Казакстан",
        "China": "Кытай",
        "Italy": "Италия",
        "Other": "",
    }

    name = models.CharField("Название бренда", max_length=120)
    country = models.CharField(
        "Страна", max_length=20, choices=Country.choices, default=Country.GERMANY
    )
    logo = models.ImageField(
        "Логотип", upload_to="brands/", validators=image_validators()
    )
    description_ru = models.TextField("Описание (русский)", blank=True)
    description_ky = models.TextField("Описание (кыргызча)", blank=True)

    class Meta(SortablePublishable.Meta):
        verbose_name = "Бренд химии"
        verbose_name_plural = "Бренды химии"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        optimize_image(self.logo, max_side=600)
        super().save(*args, **kwargs)


# ---------- Telegram-бот для отзывов (content/management/commands/run_telegram_bot.py) ----------


class TelegramEditor(models.Model):
    """Кто может публиковать отзывы через бота. Появляется по приглашению."""

    telegram_id = models.BigIntegerField("Telegram ID", unique=True)
    name = models.CharField("Имя", max_length=120, blank=True)
    is_active = models.BooleanField(
        "Доступ разрешён", default=True, help_text="Снимите, чтобы закрыть доступ к боту."
    )
    created_at = models.DateTimeField("Добавлен", auto_now_add=True)

    class Meta:
        verbose_name = "Редактор в Telegram"
        verbose_name_plural = "Редакторы в Telegram"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name or str(self.telegram_id)


def new_invite_code():
    return secrets.token_urlsafe(12)


class TelegramInvite(models.Model):
    """Одноразовая ссылка t.me/<бот>?start=<code>, по которой бот даёт доступ."""

    code = models.CharField(max_length=40, unique=True, default=new_invite_code, editable=False)
    note = models.CharField("Для кого", max_length=120, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    used_at = models.DateTimeField("Использовано", null=True, blank=True, editable=False)
    used_by = models.ForeignKey(
        TelegramEditor,
        verbose_name="Кто вошёл",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        editable=False,
    )

    class Meta:
        verbose_name = "Приглашение в бота"
        verbose_name_plural = "Приглашения в бота"
        ordering = ["-created_at"]

    def __str__(self):
        return self.note or self.code

