from rest_framework import routers
from django.urls import path, include
from .views import *

router = routers.DefaultRouter()
router.register(r"items", ItemViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path('import/', ItemImportView.as_view(), name='item_import'),
    path('import_from_site/', upload_items_view, name='upload_items'),
    path('itemslist/', ItemsListView.as_view(), name='item_list'),
    path('partnerslist/', PartnersListView.as_view(), name='partner_list'),
    path('feedbacklist/', FeedbackListView.as_view(), name='feedback_list'),
    path('useproductlist/', UseproductListView.as_view(), name='useproduct_list'),
    path('backgroundimagelist/', BackgroundImageView.as_view(), name='backgroundimage_list'),
    path('doiposlelist/', DoiposleListView.as_view(), name='doiposle_list'),
]
    