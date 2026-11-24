from rest_framework import routers
from django.urls import path, include
from .views import ItemImportView, ItemsListView, ItemViewSet, upload_items_view

router = routers.DefaultRouter()
router.register(r"items", ItemViewSet)

# Отзывы, «до/после», партнёры, услуги и бренды отдаются одним запросом:
# GET /api/content/ (приложение content).
urlpatterns = [
    path("", include(router.urls)),
    path('import/', ItemImportView.as_view(), name='item_import'),
    path('import_from_site/', upload_items_view, name='upload_items'),
    path('itemslist/', ItemsListView.as_view(), name='item_list'),
]
