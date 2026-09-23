from django.conf import settings
from django.db import models
from apps.common.models import Entity
from apps.catalog.models import amount


class Sale(Entity):
    class Channel(models.TextChoices):
        DIRECT = "direct", "Boca a boca"
        ML = "mercado_livre", "Mercado Livre"
        SHOPEE = "shopee", "Shopee"
        OTHER = "other", "Outro"

    channel = models.CharField(max_length=20, choices=Channel.choices)
    reference = models.CharField(max_length=100, blank=True)
    idempotency_key = models.UUIDField(unique=True)
    request_hash = models.CharField(max_length=64)
    gross = amount()
    discount = amount()
    platform_fee = amount()
    shipping_cost = amount()
    cost_total = amount()
    net = models.DecimalField(max_digits=14, decimal_places=2)
    profit = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(
        max_length=12, default="confirmed", choices=[("confirmed", "Confirmada"), ("cancelled", "Cancelada")]
    )
    received_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        ordering = ["-created_at", "-id"]


class SaleItem(Entity):
    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name="items")
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
    product_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    unit_price = amount()
    unit_cost = amount()
    cost_total = amount()

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name="sale_quantity_positive"),
            models.UniqueConstraint(fields=["sale", "product"], name="sale_product_unique"),
        ]
