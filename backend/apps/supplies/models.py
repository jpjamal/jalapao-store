from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.functions import Lower

from apps.catalog.models import amount
from apps.common.models import Entity
from apps.supplies.domain.pricing import price_per_gram, price_per_kg


class SupplyCategory(Entity):
    """Categoria de insumo (spec 024), separada das categorias de produto.
    `is_filament` diz que os insumos dela são filamento, com material, cor e dados do rolo."""

    name = models.CharField(max_length=100)
    is_filament = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "id"]
        verbose_name_plural = "supply categories"
        constraints = [models.UniqueConstraint(Lower("name"), name="supply_category_name_unique_ci")]

    def __str__(self):
        return self.name


class Supply(Entity):
    """Insumo: o que a loja consome para fabricar, embalar, enviar ou operar. Não é produto:
    não tem SKU nem preço de venda e nunca aparece em vendas ou anúncios."""

    category = models.ForeignKey(SupplyCategory, on_delete=models.PROTECT, related_name="supplies")
    name = models.CharField(max_length=120)
    unit = models.CharField(max_length=30, default="unidade")
    notes = models.CharField(max_length=500, blank=True)
    active = models.BooleanField(default=True)
    # só para categoria de filamento
    material = models.CharField(max_length=40, blank=True)
    color = models.CharField(max_length=40, blank=True)
    roll_weight_g = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True, validators=[MinValueValidator(Decimal("0.001"))]
    )
    roll_price = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )

    class Meta:
        ordering = ["name", "id"]
        verbose_name_plural = "supplies"
        constraints = [
            models.UniqueConstraint(Lower("name"), "category", name="supply_name_unique_ci_per_category")
        ]

    def __str__(self):
        return self.name

    @property
    def price_per_gram(self):
        if self.roll_price is None or not self.roll_weight_g:
            return None
        return price_per_gram(self.roll_price, self.roll_weight_g)

    @property
    def price_per_kg(self):
        if self.roll_price is None or not self.roll_weight_g:
            return None
        return price_per_kg(self.roll_price, self.roll_weight_g)


class SupplyStock(models.Model):
    """Saldo de um insumo: só quantidade inteira (rolos, unidades), sem custo médio."""

    supply = models.OneToOneField(Supply, primary_key=True, on_delete=models.PROTECT, related_name="stock")
    quantity = models.PositiveIntegerField(default=0)
    version = models.PositiveBigIntegerField(default=0)


class SupplyReceipt(Entity):
    """Compra de insumo (spec 024). Cancelar não apaga: a compra fica marcada como cancelada."""

    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmada"
        CANCELLED = "cancelled", "Cancelada"

    supply = models.ForeignKey(Supply, on_delete=models.PROTECT, related_name="receipts")
    supply_name = models.CharField(max_length=120)
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
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.CONFIRMED)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    # preço do rolo antes da compra, para voltar a ele ao cancelar (só filamento)
    previous_roll_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name="supply_receipt_quantity_positive"),
            models.CheckConstraint(
                condition=models.Q(unit_cost__gte=0, total__gte=0), name="supply_receipt_cost_nonnegative"
            ),
        ]


class SupplyMovement(Entity):
    """Razão imutável do saldo de um insumo: toda compra, baixa, ajuste e cancelamento."""

    supply = models.ForeignKey(Supply, on_delete=models.PROTECT, related_name="movements")
    delta = models.IntegerField()
    balance_after = models.PositiveIntegerField()
    reason = models.CharField(max_length=240)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    # a movimentação de entrada da compra (as de cancelamento e ajuste não têm)
    receipt = models.OneToOneField(
        SupplyReceipt, null=True, blank=True, on_delete=models.PROTECT, related_name="movement"
    )
    # reservado para a etapa 3 (insumos usados na venda); sem uso por enquanto
    sale = models.ForeignKey(
        "sales.Sale", null=True, blank=True, on_delete=models.PROTECT, related_name="supply_movements"
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [models.CheckConstraint(condition=~models.Q(delta=0), name="supply_movement_nonzero")]
