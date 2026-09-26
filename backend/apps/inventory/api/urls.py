"""Rotas do estoque: ajustes (movimentações) e entradas de compra ou produção."""
from rest_framework.routers import SimpleRouter

from apps.inventory.api.views import MovementViewSet, ReceiptViewSet

router = SimpleRouter()
router.register("movements", MovementViewSet)
router.register("receipts", ReceiptViewSet)
urlpatterns = router.urls
