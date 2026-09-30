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
    receipt = models.OneToOneField(
        "inventory.Receipt", null=True, blank=True, on_delete=models.PROTECT, related_name="payment"
    )
    # estorno da compra cancelada (spec 023); separado de `receipt`, que é o pagamento
    refund_of_receipt = models.OneToOneField(
        "inventory.Receipt", null=True, blank=True, on_delete=models.PROTECT, related_name="refund"
    )
    # pagamento e estorno da compra de insumo (spec 024)
    supply_receipt = models.OneToOneField(
        "supplies.SupplyReceipt", null=True, blank=True, on_delete=models.PROTECT, related_name="payment"
    )
    refund_of_supply_receipt = models.OneToOneField(
        "supplies.SupplyReceipt", null=True, blank=True, on_delete=models.PROTECT, related_name="refund"
    )

    class Meta:
        ordering = ["-occurred_on", "-created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name="cash_amount_positive"),
            models.UniqueConstraint(fields=["sale", "direction"], name="cash_sale_direction_unique"),
            models.CheckConstraint(
                condition=models.Q(sale__isnull=True) | models.Q(receipt__isnull=True),
                name="cash_single_origin",
            ),
            models.CheckConstraint(
                condition=models.Q(supply_receipt__isnull=True)
                | (models.Q(sale__isnull=True) & models.Q(receipt__isnull=True)),
                name="cash_supply_single_origin",
            ),
        ]
