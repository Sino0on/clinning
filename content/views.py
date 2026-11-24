from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BeforeAfter, ChemicalBrand, Partner, Review, Service, ServicePage
from .serializers import (
    BeforeAfterSerializer,
    ChemicalBrandSerializer,
    PartnerSerializer,
    ReviewSerializer,
    ServicePageSerializer,
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
                    Service.objects.filter(is_published=True).select_related("page"),
                    many=True,
                ).data,
                "partners": PartnerSerializer(
                    Partner.objects.filter(is_published=True), many=True
                ).data,
                "brands": ChemicalBrandSerializer(
                    ChemicalBrand.objects.filter(is_published=True), many=True
                ).data,
            }
        )


class ServicePagesView(APIView):
    """GET /api/content/pages/ — опубликованные страницы услуг целиком.

    Страниц немного, поэтому сайт берёт их одним запросом и сам выбирает
    нужную по адресу (slug).
    """

    permission_classes = [AllowAny]

    def get(self, request):
        pages = ServicePage.objects.filter(is_published=True).prefetch_related(
            "faq", "before_after"
        )
        return Response(ServicePageSerializer(pages, many=True).data)
