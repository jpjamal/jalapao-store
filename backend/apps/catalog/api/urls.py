"""Rotas do catálogo: categorias, produtos, fotos e rascunhos de anúncio."""
from rest_framework.routers import SimpleRouter

from apps.catalog.api.views import CategoryViewSet, ListingDraftViewSet, ProductImageViewSet, ProductViewSet

router = SimpleRouter()
router.register("categories", CategoryViewSet)
router.register("products", ProductViewSet)
router.register("product-images", ProductImageViewSet)
router.register("listing-drafts", ListingDraftViewSet)
urlpatterns = router.urls
