from django.conf import settings
from django.db import models
from apps.common.models import Entity


class Stock(models.Model):
    product = models.OneToOneField(
        "catalog.Product", primary_key=True, on_delete=models.PROTECT, related_name="stock"
    )
    quantity = models.PositiveIntegerField(default=0)
    version = models.PositiveBigIntegerField(default=0)


class Movement(Entity):
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="movements")
    delta = models.IntegerField()
    balance_after = models.PositiveIntegerField()
    reason = models.CharField(max_length=240)
    sale = models.ForeignKey("sales.Sale", null=True, blank=True, on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [models.CheckConstraint(condition=~models.Q(delta=0), name="movement_nonzero")]
