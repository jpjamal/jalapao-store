from decimal import Decimal
import re
import unicodedata
import uuid
from django.db import models
from django.db import transaction
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.common.models import Entity
from .domain import printing_cost


def amount(default=0):
    return models.DecimalField(
        max_digits=14, decimal_places=2, default=default, validators=[MinValueValidator(0)]
    )


def sku_initials(name):
    normalized = unicodedata.normalize("NFKD", name)
    words = re.findall(r"[A-Z0-9]+", "".join(c for c in normalized if not unicodedata.combining(c)).upper())
    initials = "".join(word[0] for word in words if word not in {"A", "AS", "DA", "DAS", "DE", "DO", "DOS", "E", "O", "OS", "PARA"})
    return initials[:6] or "PRD"


class SkuSequence(models.Model):
    """Reserva um número único e crescente para cada novo SKU automático."""

    id = models.BigAutoField(primary_key=True)


class Product(Entity):
    class Kind(models.TextChoices):
        PRINTING = "printing", "Impressão 3D"
        RESALE = "resale", "Revenda"

    sku = models.CharField(max_length=80, unique=True, blank=True)
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

    def save(self, *args, **kwargs):
        if self._state.adding and not self.sku:
            with transaction.atomic():
                while True:
                    number = SkuSequence.objects.create().pk
                    candidate = f"SKU-{sku_initials(self.name)}-{number:04d}"
                    if not Product.objects.filter(sku=candidate).exists():
                        self.sku = candidate
                        return super().save(*args, **kwargs)
        return super().save(*args, **kwargs)


def product_image_path(instance, filename):
    extension = filename.rsplit(".", 1)[-1].lower()
    return f"products/{instance.product_id}/{uuid.uuid4().hex}.{extension}"


class ProductImage(Entity):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="images")
    file = models.ImageField(upload_to=product_image_path)
    mime_type = models.CharField(max_length=20)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    size_bytes = models.PositiveIntegerField()
    alt_text = models.CharField(max_length=200, blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "created_at", "id"]


class ListingDraft(Entity):
    class Channel(models.TextChoices):
        ML = "mercado_livre", "Mercado Livre"
        SHOPEE = "shopee", "Shopee"

    class Condition(models.TextChoices):
        NEW = "new", "Novo"
        USED = "used", "Usado"
        RECONDITIONED = "reconditioned", "Recondicionado"

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="drafts")
    channel = models.CharField(max_length=30, choices=Channel.choices)
    title = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    condition = models.CharField(max_length=20, choices=Condition.choices, blank=True)
    category_id = models.CharField(max_length=80, blank=True)
    attributes = models.JSONField(default=dict, blank=True)
    images = models.ManyToManyField(ProductImage, through="ListingDraftImage", related_name="drafts")

    class Meta:
        ordering = ["-updated_at", "id"]
        # publicar cria anúncio de verdade: permissão à parte de "alterar rascunho"
        permissions = [("publish_listingdraft", "Pode publicar rascunho no marketplace")]
        constraints = [
            models.UniqueConstraint(fields=["product", "channel"], name="draft_product_channel_unique"),
            models.CheckConstraint(
                condition=models.Q(price__isnull=True) | models.Q(price__gte=0),
                name="draft_price_nonnegative",
            ),
        ]


class ListingDraftImage(models.Model):
    draft = models.ForeignKey(ListingDraft, on_delete=models.CASCADE, related_name="ordered_images")
    image = models.ForeignKey(ProductImage, on_delete=models.PROTECT)
    position = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(fields=["draft", "image"], name="draft_image_unique"),
            models.UniqueConstraint(fields=["draft", "position"], name="draft_image_position_unique"),
        ]


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
