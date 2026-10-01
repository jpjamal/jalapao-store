"""Rotas do caixa: lançamentos, categorias e resumo por categoria."""
from rest_framework.routers import SimpleRouter

from apps.finance.api.views import CashCategoryViewSet, CashViewSet

router = SimpleRouter()
router.register("cash-categories", CashCategoryViewSet)
router.register("cash", CashViewSet)
urlpatterns = router.urls
