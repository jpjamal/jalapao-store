from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import IsAdminUser
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from apps.accounts.api import LoginView, MeView
from apps.catalog.api import ProductViewSet
from apps.inventory.api import MovementViewSet, ReceiptViewSet
from apps.sales.api import SaleViewSet
from apps.finance.api import CashViewSet
from apps.common.api import health, DashboardView

router = DefaultRouter()
router.register("products", ProductViewSet)
router.register("movements", MovementViewSet)
router.register("receipts", ReceiptViewSet)
router.register("sales", SaleViewSet)
router.register("cash", CashViewSet)
urlpatterns = [
    path("health/", health),
    path("jalapao-store/admin/", admin.site.urls),
    path("api/v1/auth/token/", LoginView.as_view()),
    path("api/v1/auth/refresh/", TokenRefreshView.as_view()),
    path("api/v1/auth/logout/", TokenBlacklistView.as_view()),
    path("api/v1/auth/me/", MeView.as_view()),
    path("api/v1/dashboard/", DashboardView.as_view()),
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
    path("api/v1/", include(router.urls)),
]
