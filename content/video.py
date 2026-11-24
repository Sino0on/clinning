"""Фоновая обработка видео-отзывов: сжатие для сайта и обложка.

Видео с телефона весит 50–300 МБ. Для сайта его ужимаем до ~5 МБ:
H.264 + AAC, не больше 960 px по длинной стороне, moov-атом в начале
файла (faststart: видео стартует без скачивания целиком).

Сжатие идёт отдельным процессом, чтобы сохранение в админке не ждало
1–3 минуты. Если обработка прервалась (например, перезапуск контейнера),
её можно повторить действием в админке или командой
`python manage.py process_videos`.
"""

import logging
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.files import File

logger = logging.getLogger(__name__)

MAX_SIDE = 960
MAX_SECONDS = 300  # длиннее 5 минут для отзыва не бывает — обрезаем


def start_video_processing(review_id):
    """Запускает `manage.py process_videos --id N` в фоне и сразу возвращается."""
    log_dir = Path(settings.BASE_DIR) / "logs"
    log_dir.mkdir(exist_ok=True)
    cmd = [sys.executable, "manage.py", "process_videos", "--id", str(review_id)]
    if shutil.which("nice"):
        # Сервер общий: не отнимаем процессор у соседних проектов
        cmd = ["nice", "-n", "10", *cmd]
    with open(log_dir / "video.log", "ab") as log:
        subprocess.Popen(
            cmd,
            cwd=settings.BASE_DIR,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )


def _ffmpeg(*args):
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=1200,
    )


def process_review_video(review):
    from .models import Review

    src = Path(review.file.path)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "video.mp4"
        poster = Path(tmp) / "poster.jpg"
        try:
            _ffmpeg(
                "-i", str(src),
                "-t", str(MAX_SECONDS),
                "-vf",
                f"scale='min(iw,{MAX_SIDE})':'min(ih,{MAX_SIDE})':force_original_aspect_ratio=decrease,"
                "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                "-c:v", "libx264", "-preset", "faster", "-crf", "28",
                "-profile:v", "high", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "96k",
                "-movflags", "+faststart",
                "-threads", "2",
                str(out),
            )
            try:
                _ffmpeg("-ss", "1", "-i", str(out), "-frames:v", "1", "-q:v", "3", str(poster))
            except subprocess.CalledProcessError:
                _ffmpeg("-i", str(out), "-frames:v", "1", "-q:v", "3", str(poster))

            original = review.file.name
            name = uuid4().hex
            with open(out, "rb") as f:
                review.file.save(f"{name}.mp4", File(f), save=False)
            with open(poster, "rb") as f:
                review.poster.save(f"{name}.jpg", File(f), save=False)
            review.status = Review.Status.READY
            review.error = ""
            review.save()
            if original != review.file.name:
                review.file.storage.delete(original)
            logger.info("Видео-отзыв %s обработан", review.pk)
        except subprocess.CalledProcessError as e:
            _fail(review, (e.stderr or str(e))[-1000:])
        except Exception as e:  # noqa: BLE001 — любую ошибку показываем в админке
            _fail(review, str(e)[-1000:])


def _fail(review, message):
    from .models import Review

    logger.error("Видео-отзыв %s: ошибка обработки: %s", review.pk, message)
    review.status = Review.Status.FAILED
    review.error = message
    review.save(update_fields=["status", "error", "updated_at"])
