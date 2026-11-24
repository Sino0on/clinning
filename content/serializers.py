from django.conf import settings
from rest_framework import serializers

from .models import BeforeAfter, ChemicalBrand, Partner, Review, Service


def absolute_media_url(field_file):
    """Полный URL файла: сайт (Next.js) живёт на другом домене."""
    if not field_file:
        return None
    return f"{settings.PUBLIC_BASE_URL}{field_file.url}"


class MediaUrlField(serializers.Field):
    def __init__(self, **kwargs):
        kwargs["read_only"] = True
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        return getattr(instance, self.source)

    def to_representation(self, value):
        return absolute_media_url(value)


class ReviewSerializer(serializers.ModelSerializer):
    file = MediaUrlField()
    poster = MediaUrlField()

    class Meta:
        model = Review
        fields = ["id", "kind", "file", "poster", "caption_ru", "caption_ky"]


class BeforeAfterSerializer(serializers.ModelSerializer):
    before = MediaUrlField()
    after = MediaUrlField()

    class Meta:
        model = BeforeAfter
        fields = [
            "id",
            "title_ru",
            "title_ky",
            "description_ru",
            "description_ky",
            "before",
            "after",
        ]


class ServiceSerializer(serializers.ModelSerializer):
    image = MediaUrlField()

    class Meta:
        model = Service
        fields = [
            "id",
            "title_ru",
            "title_ky",
            "duration_ru",
            "duration_ky",
            "description_ru",
            "description_ky",
            "image",
        ]


class PartnerSerializer(serializers.ModelSerializer):
    logo = MediaUrlField()

    class Meta:
        model = Partner
        fields = ["id", "name", "logo", "link"]


class ChemicalBrandSerializer(serializers.ModelSerializer):
    logo = MediaUrlField()
    country_ru = serializers.CharField(source="get_country_display", read_only=True)
    country_ky = serializers.SerializerMethodField()

    class Meta:
        model = ChemicalBrand
        fields = [
            "id",
            "name",
            "country",
            "country_ru",
            "country_ky",
            "logo",
            "description_ru",
            "description_ky",
        ]

    def get_country_ky(self, obj):
        return ChemicalBrand.COUNTRY_KY.get(obj.country, "")
