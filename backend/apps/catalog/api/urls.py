"""Rotas do catálogo: produtos, fotos e rascunhos de anúncio."""
from rest_framework.routers import SimpleRouter

from apps.catalog.api.views import ListingDraftViewSet, ProductImageViewSet, ProductViewSet

router = SimpleRouter()
router.register("products", ProductViewSet)
router.register("product-images", ProductImageViewSet)
router.register("listing-drafts", ListingDraftViewSet)
urlpatterns = router.urls
