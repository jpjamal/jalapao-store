from django.conf import settings
from django.db import models
from django.db.models.functions import Lower
from apps.common.models import Entity
from apps.catalog.models import amount
from apps.finance.domain.categories import SYSTEM_CATEGORIES, origin_of, system_key_for


class CashCategory(Entity):
    """Categoria de lançamento do Caixa (spec 026). `counts_in_result` separa despesa de movimentação de
    dinheiro: energia e impostos podem contar, empréstimo, aporte e retirada do dono não. As categorias do
    sistema (`system_key`) são só dos lançamentos automáticos e não são editáveis."""

    class Direction(models.TextChoices):
        IN = "in", "Entrada"
        OUT = "out", "Saída"
        BOTH = "both", "Entrada ou saída"

    name = models.CharField(max_length=100)
    direction = models.CharField(max_length=4, choices=Direction.choices)
    counts_in_result = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    system_key = models.CharField(max_length=30, unique=True, null=True, blank=True)

    class Meta:
        ordering = ["name", "id"]
        verbose_name_plural = "cash categories"
        constraints = [models.UniqueConstraint(Lower("name"), name="cash_category_name_unique_ci")]

    def __str__(self):
        return self.name

    @property
    def is_system(self):
        return self.system_key is not None


def system_category(key):
    """Categoria do sistema pela chave; cria se não existir (banco zerado)."""
    name, direction = SYSTEM_CATEGORIES[key]
    found = CashCategory.objects.filter(system_key=key).first()
    return found or CashCategory.objects.create(
        name=name, direction=direction, counts_in_result=False, system_key=key
    )


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
    sale_revision = models.OneToOneField(
        "sales.SaleRevision", null=True, blank=True, on_delete=models.PROTECT, related_name="cash_adjustment"
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
    category = models.ForeignKey(CashCategory, on_delete=models.PROTECT, related_name="entries")

    @property
    def origin(self):
        return origin_of(
            direction=self.direction,
            sale=self.sale_id,
            sale_revision=self.sale_revision_id,
            receipt=self.receipt_id,
            refund_of_receipt=self.refund_of_receipt_id,
            supply_receipt=self.supply_receipt_id,
            refund_of_supply_receipt=self.refund_of_supply_receipt_id,
        )

    def save(self, *args, **kwargs):
        # lançamento automático recebe a categoria do sistema pela origem; manual sem categoria cai em
        # "A classificar" (a API exige categoria no manual, então isto só vale para código interno)
        if self.category_id is None:
            self.category = system_category(system_key_for(self.origin))
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-occurred_on", "-created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name="cash_amount_positive"),
            models.UniqueConstraint(
                fields=["sale", "direction"], condition=models.Q(sale_revision__isnull=True),
                name="cash_sale_direction_unique",
            ),
            models.CheckConstraint(
                condition=models.Q(sale_revision__isnull=True) | models.Q(sale__isnull=False),
                name="cash_revision_requires_sale",
            ),
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
