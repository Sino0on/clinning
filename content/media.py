"""Проверка и подготовка загружаемых файлов."""

from io import BytesIO
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible
from PIL import Image, ImageOps

IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]
VIDEO_EXTENSIONS = ["mp4", "mov", "m4v", "webm", "avi", "mkv", "3gp"]
MAX_IMAGE_MB = 25
MAX_VIDEO_MB = 300


@deconstructible
class MaxFileSizeValidator:
    """Ограничение размера файла (деконструируемое — для миграций)."""

    def __init__(self, max_mb):
        self.max_mb = max_mb

    def __call__(self, f):
        if f.size > self.max_mb * 1024 * 1024:
            raise ValidationError(f"Файл слишком большой: максимум {self.max_mb} МБ.")

    def __eq__(self, other):
        return isinstance(other, MaxFileSizeValidator) and self.max_mb == other.max_mb


def validate_review_file_size(f):
    ext = f.name.rsplit(".", 1)[-1].lower()
    limit = MAX_VIDEO_MB if ext in VIDEO_EXTENSIONS else MAX_IMAGE_MB
    MaxFileSizeValidator(limit)(f)


def image_validators():
    return [
        FileExtensionValidator(
            IMAGE_EXTENSIONS,
            message="Нужна картинка JPG, PNG или WEBP. Фото с iPhone (HEIC) сохраните как JPG.",
        ),
        MaxFileSizeValidator(MAX_IMAGE_MB),
    ]


def review_file_validators():
    return [
        FileExtensionValidator(
            IMAGE_EXTENSIONS + VIDEO_EXTENSIONS,
            message="Нужно фото (JPG, PNG, WEBP) или видео (MP4, MOV).",
        ),
        validate_review_file_size,
    ]


def _has_transparency(img):
    if img.mode in ("RGBA", "LA"):
        return img.getchannel("A").getextrema()[0] < 255
    return img.mode == "P" and "transparency" in img.info


def optimize_image(field_file, max_side):
    """Пережимает только что загруженную картинку прямо перед сохранением.

    Поворот по EXIF (фото с телефона не лягут на бок), уменьшение до
    max_side по длинной стороне, JPEG 85 или PNG, если есть прозрачность
    (логотипы). Уже сохранённые файлы не трогает.
    """
    if not field_file or getattr(field_file, "_committed", True):
        return

    source = field_file.file
    source.seek(0)
    img = Image.open(source)
    img = ImageOps.exif_transpose(img)
    transparent = _has_transparency(img)
    img.thumbnail((max_side, max_side), Image.LANCZOS)

    buf = BytesIO()
    if transparent:
        img.convert("RGBA").save(buf, "PNG", optimize=True)
        ext = "png"
    else:
        img.convert("RGB").save(buf, "JPEG", quality=85, optimize=True, progressive=True)
        ext = "jpg"

    field_file.save(f"{uuid4().hex}.{ext}", ContentFile(buf.getvalue()), save=False)
