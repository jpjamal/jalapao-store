from django.conf import settings
from django.db import models
from apps.common.models import Entity
from apps.catalog.models import amount


class CashEntry(Entity):
    class Direction(models.TextChoices):
        IN = "in", "Entrada"
        OUT = "out", "Saída"

    direction = models.CharField(max_length=3, choices=Direction.choices)
    amount = amount()
    description = models.CharField(max_length=240)
    occurred_on = models.DateField()
    sale = models.ForeignKey(
        "sales.Sale", null=True, blank=True, on_delete=models.PROTECT, related_name="cash_entries"
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        ordering = ["-occurred_on", "-created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name="cash_amount_positive"),
            models.UniqueConstraint(fields=["sale", "direction"], name="cash_sale_direction_unique"),
        ]
