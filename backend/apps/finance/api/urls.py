"""Rotas do caixa."""
from rest_framework.routers import SimpleRouter

from apps.finance.api.views import CashViewSet

router = SimpleRouter()
router.register("cash", CashViewSet)
urlpatterns = router.urls
