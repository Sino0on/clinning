from django.contrib import admin
from django.urls import path
from django.urls import include
from rest_framework import routers
from api.views import ItemViewSet

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
]
