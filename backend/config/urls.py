"""Raiz das rotas: cada contexto declara as suas em `apps/<contexto>/api/urls.py`."""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.common.api.views import health

CONTEXTOS = ["accounts", "common", "catalog", "inventory", "sales", "finance", "integrations"]

urlpatterns = [
    path("health/", health),
    path("jalapao-store/admin/", admin.site.urls),
    path(
        "api/v1/schema/",
        SpectacularAPIView.as_view(
            permission_classes=[IsAdminUser],
            authentication_classes=[SessionAuthentication, JWTAuthentication],
        ),
        name="schema",
    ),
    path(
        "api/v1/docs/",
        SpectacularSwaggerView.as_view(
            url="/jalapao-store/backend-api/schema/",
            permission_classes=[IsAdminUser],
            authentication_classes=[SessionAuthentication, JWTAuthentication],
        ),
    ),
    *[path("api/v1/", include(f"apps.{contexto}.api.urls")) for contexto in CONTEXTOS],
]
