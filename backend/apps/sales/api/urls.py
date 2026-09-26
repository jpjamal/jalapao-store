"""Rotas de vendas, incluindo a importação de pedidos do Mercado Livre."""
from rest_framework.routers import SimpleRouter

from apps.sales.api.views import SaleViewSet

router = SimpleRouter()
router.register("sales", SaleViewSet)
urlpatterns = router.urls
