from rest_framework import routers
from django.urls import path, include
from .views import ItemViewSet, ItemImportView, upload_items_view, ItemsListView

router = routers.DefaultRouter()
router.register(r"items", ItemViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path('import/', ItemImportView.as_view(), name='item_import'),
    path('import_from_site/', upload_items_view, name='upload_items'),
    path('itemslist/', ItemsListView.as_view(), name='item_list')
]
    