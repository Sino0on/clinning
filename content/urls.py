from django.urls import path

from .views import ServicePagesView, SiteContentView

urlpatterns = [
    path("", SiteContentView.as_view(), name="site_content"),
    path("pages/", ServicePagesView.as_view(), name="service_pages"),
]
