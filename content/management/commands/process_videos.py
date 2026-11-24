from django.core.management.base import BaseCommand

from content.models import Review
from content.video import process_review_video


class Command(BaseCommand):
    help = "Сжимает загруженные видео-отзывы для сайта и делает обложки"

    def add_arguments(self, parser):
        parser.add_argument("--id", type=int, help="Обработать только этот отзыв")

    def handle(self, *args, **options):
        reviews = Review.objects.filter(
            kind=Review.Kind.VIDEO, status=Review.Status.PROCESSING
        )
        if options["id"]:
            reviews = reviews.filter(pk=options["id"])
        for review in reviews:
            self.stdout.write(f"Обрабатываю отзыв {review.pk}...")
            process_review_video(review)
            review.refresh_from_db()
            self.stdout.write(f"  {review.get_status_display()}")
