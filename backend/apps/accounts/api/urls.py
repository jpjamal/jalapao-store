"""Rotas de autenticação (JWT em cookie, pelo BFF do frontend)."""
from django.urls import path
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from apps.accounts.api.views import LoginView, MeView

urlpatterns = [
    path("auth/token/", LoginView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("auth/logout/", TokenBlacklistView.as_view()),
    path("auth/me/", MeView.as_view()),
]
