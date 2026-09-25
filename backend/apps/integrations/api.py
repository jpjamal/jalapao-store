from django.core.exceptions import ValidationError
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.common.permissions import ModelPermissions

from .base import IntegrationError
from .models import Listing, MarketplaceAccount
from .services import (
    conectar,
    conectar_ml,
    enviar_estoque,
    importar_anuncios,
    iniciar_oauth_ml,
    link_de_autorizacao,
    situacao,
)


def _traduzir(chamada):
    """Erro de integração vira 400 com texto legível, não 500 com stacktrace."""
    try:
        return chamada()
    except IntegrationError as e:
        raise ValidationError({"integration": str(e)}) from e


class AccountSerializer(serializers.ModelSerializer):
    channel_label = serializers.CharField(source="get_channel_display", read_only=True)
    token_valido = serializers.BooleanField(read_only=True)
    authorization_days_left = serializers.IntegerField(
        source="dias_ate_expirar_autorizacao", read_only=True, allow_null=True
    )

    class Meta:
        model = MarketplaceAccount
        fields = [
            "id",
            "channel",
            "channel_label",
            "external_id",
            "name",
            "active",
            "token_valido",
            "authorization_expires_at",
            "authorization_days_left",
            "last_synced_at",
            "last_error",
            "created_at",
        ]
        read_only_fields = fields


class ListingSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    local_stock = serializers.IntegerField(source="product.stock.quantity", read_only=True)

    class Meta:
        model = Listing
        fields = [
            "id",
            "marketplace",
            "seller_id",
            "item_id",
            "title",
            "product",
            "product_name",
            "product_sku",
            "local_stock",
            "remote_stock",
            "sync_enabled",
            "stock_pushed_at",
        ]
        read_only_fields = [
            "id",
            "marketplace",
            "seller_id",
            "item_id",
            "title",
            "product_name",
            "product_sku",
            "local_stock",
            "remote_stock",
            "stock_pushed_at",
        ]

    def validate(self, attrs):
        if self.instance and self.instance.sync_enabled and attrs.get("product", self.instance.product) != self.instance.product:
            raise serializers.ValidationError({"product": "Desative a sincronia antes de trocar o produto."})
        return attrs

    def update(self, instance, validated_data):
        if (validated_data.get("sync_enabled") is True and not instance.sync_enabled) or (
            "product" in validated_data and validated_data["product"] != instance.product
        ):
            instance.last_pushed_version = None
        return super().update(instance, validated_data)


class AccountPermissions(ModelPermissions):
    """Aqui o POST não cria registro: conecta, importa, sincroniza — tudo é alteração.

    O mapa padrão do DRF manda POST pedir `add_`, o que obrigaria a dar permissão de criar
    conta para quem só vai mandar sincronizar. Mapeado para `change_`, que é o que essas
    ações realmente fazem.
    """

    perms_map = {**ModelPermissions.perms_map, "POST": ["%(app_label)s.change_%(model_name)s"]}


class AccountViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Lojas conectadas. Conectar e sincronizar exigem permissão de escrita."""

    queryset = MarketplaceAccount.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [AccountPermissions]
    filterset_fields = ["channel", "active"]

    def _exigir_escrita(self):
        if not self.request.user.has_perm("integrations.change_marketplaceaccount"):
            raise PermissionDenied()

    @extend_schema(
        parameters=[
            inline_serializer(name="AuthLinkQuery", fields={"channel": serializers.CharField()})
        ],
        responses=inline_serializer(
            name="AuthLink", fields={"url": serializers.CharField()}
        ),
    )
    @action(detail=False, methods=["get"], url_path="auth-link")
    def auth_link(self, request):
        self._exigir_escrita()
        canal = request.query_params.get("channel", MarketplaceAccount.Channel.SHOPEE)
        if canal == MarketplaceAccount.Channel.ML:
            raise ValidationError({"channel": "Use ml-auth-link para iniciar o OAuth seguro."})
        url = _traduzir(lambda: link_de_autorizacao(canal))
        return Response({"url": url})

    @extend_schema(request=None, responses=inline_serializer(
        name="MlAuthLink", fields={"url": serializers.CharField()},
    ))
    @action(detail=False, methods=["post"], url_path="ml-auth-link")
    def ml_auth_link(self, request):
        self._exigir_escrita()
        return Response({"url": _traduzir(lambda: iniciar_oauth_ml(request.user))})

    @extend_schema(
        request=inline_serializer(
            name="ConnectRequest",
            fields={
                "channel": serializers.CharField(),
                "code": serializers.CharField(),
                "external_id": serializers.CharField(),
                "state": serializers.CharField(),
            },
        ),
        responses=AccountSerializer,
    )
    @action(detail=False, methods=["post"])
    def connect(self, request):
        self._exigir_escrita()
        dados = request.data or {}
        canal = dados.get("channel") or MarketplaceAccount.Channel.SHOPEE
        obrigatorios = ("code", "state") if canal == MarketplaceAccount.Channel.ML else ("code", "external_id")
        for campo in obrigatorios:
            if not dados.get(campo):
                raise ValidationError({campo: "Campo obrigatório."})
        if canal == MarketplaceAccount.Channel.ML:
            conta = _traduzir(lambda: conectar_ml(
                user=request.user, code=dados["code"], state=dados["state"],
            ))
        else:
            conta = _traduzir(
                lambda: conectar(
                    canal=canal,
                    code=dados["code"],
                    external_id=str(dados["external_id"]),
                )
            )
        return Response(AccountSerializer(conta).data)

    @extend_schema(
        request=None,
        responses=inline_serializer(
            name="ImportResult",
            fields={
                "total": serializers.IntegerField(),
                "vinculos_novos": serializers.IntegerField(),
                "pendentes": serializers.ListField(child=serializers.DictField()),
            },
        ),
    )
    @action(detail=True, methods=["post"], url_path="import-listings")
    def import_listings(self, request, pk=None):
        self._exigir_escrita()
        return Response(_traduzir(lambda: importar_anuncios(self.get_object())))

    @extend_schema(
        request=None,
        responses=inline_serializer(
            name="PushStockResult",
            fields={
                "enviados": serializers.IntegerField(),
                "ignorados": serializers.IntegerField(),
                "falhas": serializers.ListField(child=serializers.CharField()),
            },
        ),
    )
    @action(detail=True, methods=["post"], url_path="push-stock")
    def push_stock(self, request, pk=None):
        self._exigir_escrita()
        return Response(_traduzir(lambda: enviar_estoque(self.get_object())))

    @extend_schema(
        responses=inline_serializer(
            name="AccountStatus",
            fields={"accounts": serializers.ListField(child=serializers.DictField())},
        )
    )
    @action(detail=False, methods=["get"])
    def status(self, request):
        return Response(
            {"accounts": [situacao(c) for c in MarketplaceAccount.objects.filter(active=True)]}
        )

    # ---------- pesquisa de preços no Mercado Livre (spec 013): só leitura ----------

    @staticmethod
    def _codigo(valor, campo):
        """Códigos do Mercado Livre são letras, números e hífen — nada que mude o caminho."""
        valor = (valor or "").strip()
        if not valor or len(valor) > 40 or not valor.replace("-", "").isalnum():
            raise serializers.ValidationError({campo: "Informe um código válido."})
        return valor

    @extend_schema(
        parameters=[
            OpenApiParameter("q", str, required=False, description="Palavras do produto"),
            OpenApiParameter("gtin", str, required=False, description="Código de barras (EAN)"),
        ],
        responses=inline_serializer(
            name="PriceProducts", fields={"produtos": serializers.ListField(child=serializers.DictField())}
        ),
    )
    @action(detail=False, methods=["get"], url_path="price-products")
    def price_products(self, request):
        from .meli.pesquisa import produtos

        q = (request.query_params.get("q") or "").strip()[:200]
        gtin = (request.query_params.get("gtin") or "").strip()
        if gtin and not gtin.isdigit():
            raise serializers.ValidationError({"gtin": "O código de barras tem só números."})
        if not gtin and len(q) < 3:
            raise serializers.ValidationError({"q": "Digite ao menos 3 letras ou o código de barras."})
        return Response({"produtos": _traduzir(lambda: produtos(q=q, gtin=gtin))})

    @extend_schema(
        parameters=[OpenApiParameter("product_id", str, required=True)],
        responses=inline_serializer(
            name="PriceOffers",
            fields={
                "resumo": serializers.DictField(),
                "ofertas": serializers.ListField(child=serializers.DictField()),
            },
        ),
    )
    @action(detail=False, methods=["get"], url_path="price-offers")
    def price_offers(self, request):
        from .meli.pesquisa import ofertas

        produto_id = self._codigo(request.query_params.get("product_id"), "product_id")
        return Response(_traduzir(lambda: ofertas(produto_id)))

    @extend_schema(
        parameters=[OpenApiParameter("category_id", str, required=True)],
        responses=inline_serializer(
            name="PriceBestSellers",
            fields={
                "resumo": serializers.DictField(),
                "itens": serializers.ListField(child=serializers.DictField()),
            },
        ),
    )
    @action(detail=False, methods=["get"], url_path="price-best-sellers")
    def price_best_sellers(self, request):
        from .meli.pesquisa import mais_vendidos

        categoria_id = self._codigo(request.query_params.get("category_id"), "category_id")
        return Response(_traduzir(lambda: mais_vendidos(categoria_id)))


class ListingViewSet(
    mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    """Vínculos anúncio ↔ produto. O que se edita aqui é o interruptor e o produto."""

    queryset = Listing.objects.select_related("product", "product__stock").all()
    serializer_class = ListingSerializer
    filterset_fields = ["marketplace", "sync_enabled", "product"]
