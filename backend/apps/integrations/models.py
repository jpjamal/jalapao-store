from django.db import models
from apps.common.models import Entity


class Listing(Entity):
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="listings")
    marketplace = models.CharField(max_length=30, default="mercado_livre")
    seller_id = models.CharField(max_length=80)
    item_id = models.CharField(max_length=80)
    user_product_id = models.CharField(max_length=80, blank=True)
    family_id = models.CharField(max_length=80, blank=True)
    sync_enabled = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["marketplace", "seller_id", "item_id"], name="listing_external_unique"
            )
        ]


class OutboxEvent(Entity):
    """Transactional intent only. Delivery worker is deliberately not enabled yet."""

    topic = models.CharField(max_length=80)
    payload = models.JSONField()
    delivered_at = models.DateTimeField(null=True, blank=True)
