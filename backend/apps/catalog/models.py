from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.common.models import Entity
from .domain import printing_cost


def amount(default=0):
    return models.DecimalField(
        max_digits=14, decimal_places=2, default=default, validators=[MinValueValidator(0)]
    )


class Product(Entity):
    class Kind(models.TextChoices):
        PRINTING = "printing", "Impressão 3D"
        RESALE = "resale", "Revenda"

    sku = models.CharField(max_length=80, unique=True)
    legacy_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=12, choices=Kind.choices, default=Kind.RESALE)
    description = models.TextField(blank=True)
    cost_price = amount()
    sale_price = amount()
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cost_price__gte=0, sale_price__gte=0), name="product_prices_nonnegative"
            )
        ]

    def __str__(self):
        return self.name


class PrintingProfile(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="printing")
    filament_price_kg = amount(115)
    weight_g = models.DecimalField(
        max_digits=12, decimal_places=3, validators=[MinValueValidator(Decimal("0.001"))]
    )
    power_w = amount(200)
    hours = models.PositiveIntegerField(default=0)
    minutes = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(59)])
    energy_price_kwh = models.DecimalField(
        max_digits=10, decimal_places=4, default=Decimal("1.56"), validators=[MinValueValidator(0)]
    )
    labor_cost = amount()
    fixed_cost = amount()
    markup_percent = amount(100)

    def prices(self):
        return printing_cost(
            **{f.name: getattr(self, f.name) for f in self._meta.fields if f.name not in ("id", "product")}
        )
