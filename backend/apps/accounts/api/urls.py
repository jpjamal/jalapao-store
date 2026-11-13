"""Rotas de autenticação (JWT em cookie, pelo BFF do frontend)."""
from django.urls import path
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from apps.accounts.api.views import (
    ForgotPasswordView,
    LoginView,
    MeView,
    ResetPasswordView,
    ResourcesView,
)

urlpatterns = [
    path("auth/token/", LoginView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("auth/logout/", TokenBlacklistView.as_view()),
    path("auth/me/", MeView.as_view()),
    # sem login (spec 039)
    path("auth/resources/", ResourcesView.as_view()),
    path("auth/forgot-password/", ForgotPasswordView.as_view()),
    path("auth/reset-password/<str:code>/", ResetPasswordView.as_view()),
]
