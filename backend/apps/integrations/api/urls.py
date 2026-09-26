"""Rotas das integrações: contas de marketplace e vínculos de anúncio."""
from rest_framework.routers import SimpleRouter

from apps.integrations.api.views import AccountViewSet, ListingViewSet

router = SimpleRouter()
router.register("integrations", AccountViewSet)
router.register("listings", ListingViewSet)
urlpatterns = router.urls
