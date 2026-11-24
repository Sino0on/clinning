from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.urls import include

urlpatterns = [
    path("admin/", admin.site.urls),
    # Контент сайта (отзывы, до/после, услуги, партнёры, бренды) одним запросом
    path("api/content/", include("content.urls")),
    path("api/", include("api.urls")),
]

# Локальная разработка: загруженные файлы. На сервере /media/ раздаёт nginx,
# до Django такие запросы не доходят.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
