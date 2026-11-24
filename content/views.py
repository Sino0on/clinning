from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BeforeAfter, ChemicalBrand, Partner, Review, Service
from .serializers import (
    BeforeAfterSerializer,
    ChemicalBrandSerializer,
    PartnerSerializer,
    ReviewSerializer,
    ServiceSerializer,
)


class SiteContentView(APIView):
    """GET /api/content/ — весь редактируемый контент сайта одним запросом.

    Только опубликованное, в порядке из админки. Видео-отзывы — только
    уже обработанные (сжатые, с обложкой).
    """

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "reviews": ReviewSerializer(
                    Review.objects.filter(
                        is_published=True, status=Review.Status.READY
                    ),
                    many=True,
                ).data,
                "beforeAfter": BeforeAfterSerializer(
                    BeforeAfter.objects.filter(is_published=True), many=True
                ).data,
                "services": ServiceSerializer(
                    Service.objects.filter(is_published=True), many=True
                ).data,
                "partners": PartnerSerializer(
                    Partner.objects.filter(is_published=True), many=True
                ).data,
                "brands": ChemicalBrandSerializer(
                    ChemicalBrand.objects.filter(is_published=True), many=True
                ).data,
            }
        )
