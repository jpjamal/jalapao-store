"""Rotas dos insumos: categorias, insumos, compras e movimentos do saldo."""
from rest_framework.routers import SimpleRouter

from apps.supplies.api.views import (
    SupplyCategoryViewSet,
    SupplyMovementViewSet,
    SupplyReceiptViewSet,
    SupplyViewSet,
)

router = SimpleRouter()
router.register("supply-categories", SupplyCategoryViewSet)
router.register("supplies", SupplyViewSet)
router.register("supply-receipts", SupplyReceiptViewSet)
router.register("supply-movements", SupplyMovementViewSet)
urlpatterns = router.urls
