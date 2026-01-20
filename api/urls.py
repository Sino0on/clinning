from rest_framework import routers
from django.urls import path, include
from .views import ItemViewSet, ItemImportView

router = routers.DefaultRouter()
router.register(r"items", ItemViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path('import/', ItemImportView.as_view(), name='item_import'),
]
    