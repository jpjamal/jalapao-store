from django.conf import settings
from django.db import models
from apps.common.models import Entity
from apps.catalog.models import amount
from decimal import Decimal
from django.core.validators import MinValueValidator


class Stock(models.Model):
    product = models.OneToOneField(
        "catalog.Product", primary_key=True, on_delete=models.PROTECT, related_name="stock"
    )
    quantity = models.PositiveIntegerField(default=0)
    version = models.PositiveBigIntegerField(default=0)
    value = amount()

    @property
    def average_cost(self):
        return (self.value / self.quantity).quantize(Decimal("0.000001")) if self.quantity else Decimal(0)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(value__gte=0), name="stock_value_nonnegative"),
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0) | models.Q(value=0), name="empty_stock_zero_value"
            ),
        ]


class Receipt(Entity):
    class Kind(models.TextChoices):
        PURCHASE = "purchase", "Compra"
        PRODUCTION = "production", "Produção"

    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="receipts")
    product_name = models.CharField(max_length=200)
    kind = models.CharField(max_length=12, choices=Kind.choices)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_cost = amount()
    total = amount()
    occurred_on = models.DateField()
    supplier = models.CharField(max_length=200, blank=True)
    reference = models.CharField(max_length=100, blank=True)
    notes = models.CharField(max_length=500, blank=True)
    idempotency_key = models.UUIDField(unique=True)
    request_hash = models.CharField(max_length=64)
    paid_at = models.DateTimeField(null=True, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name="receipt_quantity_positive"),
            models.CheckConstraint(
                condition=models.Q(unit_cost__gte=0, total__gte=0), name="receipt_cost_nonnegative"
            ),
        ]


class Movement(Entity):
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="movements")
    delta = models.IntegerField()
    balance_after = models.PositiveIntegerField()
    reason = models.CharField(max_length=240)
    sale = models.ForeignKey("sales.Sale", null=True, blank=True, on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    receipt = models.OneToOneField(
        Receipt, null=True, blank=True, on_delete=models.PROTECT, related_name="movement"
    )
    value_delta = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    value_after = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [models.CheckConstraint(condition=~models.Q(delta=0), name="movement_nonzero")]
