from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.common.models import Entity
from .fields import EncryptedTextField


class MarketplaceAccount(Entity):
    """Uma loja conectada num marketplace.

    Serve Shopee e Mercado Livre sem mudança: os dois entregam um par de tokens com prazo e
    amarram a autorização a um identificador de loja do lado deles. O que muda é *como* o
    token é obtido, e isso mora no adaptador de cada canal.
    """

    class Channel(models.TextChoices):
        SHOPEE = "shopee", "Shopee"
        ML = "mercado_livre", "Mercado Livre"

    channel = models.CharField(max_length=30, choices=Channel.choices)
    external_id = models.CharField(max_length=80, help_text="shop_id na Shopee, user_id no ML")
    name = models.CharField(max_length=200, blank=True)

    access_token = EncryptedTextField(blank=True)
    refresh_token = EncryptedTextField(blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    # a Shopee limita a autorização a 365 dias; depois o dono precisa autorizar de novo
    authorization_expires_at = models.DateTimeField(null=True, blank=True)

    active = models.BooleanField(default=True)
    last_error = models.CharField(max_length=500, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["channel", "external_id"]
        constraints = [
            models.UniqueConstraint(fields=["channel", "external_id"], name="account_channel_unique")
        ]

    def __str__(self):
        return f"{self.get_channel_display()} · {self.name or self.external_id}"

    @property
    def token_valido(self):
        return bool(self.access_token and self.token_expires_at) and (
            self.token_expires_at > timezone.now()
        )

    @property
    def dias_ate_expirar_autorizacao(self):
        if not self.authorization_expires_at:
            return None
        return (self.authorization_expires_at - timezone.now()).days


class Listing(Entity):
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="listings")
    marketplace = models.CharField(max_length=30, default="mercado_livre")
    seller_id = models.CharField(max_length=80)
    item_id = models.CharField(max_length=80)
    user_product_id = models.CharField(max_length=80, blank=True)
    family_id = models.CharField(max_length=80, blank=True)
    sync_enabled = models.BooleanField(default=False)
    # rascunho que originou o anúncio, quando ele foi publicado por aqui (spec 012)
    draft = models.OneToOneField(
        "catalog.ListingDraft", on_delete=models.SET_NULL, null=True, blank=True, related_name="listing"
    )
    # último envio do rascunho ao anúncio, para saber se há alteração pendente
    pushed_at = models.DateTimeField(null=True, blank=True)
    # foto da loja → id da foto no marketplace, para não subir a mesma foto de novo
    picture_ids = models.JSONField(default=dict, blank=True)

    # espelho do anúncio, só para conferência na tela — não manda em nada
    title = models.CharField(max_length=300, blank=True)
    remote_stock = models.IntegerField(null=True, blank=True)
    stock_pushed_at = models.DateTimeField(null=True, blank=True)
    last_pushed_version = models.PositiveBigIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["marketplace", "item_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["marketplace", "seller_id", "item_id"], name="listing_external_unique"
            )
        ]

    def __str__(self):
        return f"{self.marketplace} · {self.item_id}"


class OutboxEvent(Entity):
    """Intenção gravada na mesma transação do fato. A entrega é de quem consome."""

    topic = models.CharField(max_length=80)
    payload = models.JSONField()
    delivered_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["created_at", "id"]


class OAuthAttempt(Entity):
    """Tentativa ML de curta duração; nunca persiste o state em texto claro."""

    state_hash = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code_verifier = EncryptedTextField(blank=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["expires_at"], name="ml_oauth_expiry_idx")]
