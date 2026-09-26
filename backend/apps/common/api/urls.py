"""Rotas transversais: o painel da visão geral."""
from django.urls import path

from apps.common.api.views import DashboardView

urlpatterns = [path("dashboard/", DashboardView.as_view())]
