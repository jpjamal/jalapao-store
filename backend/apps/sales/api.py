from rest_framework import serializers, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from .models import Sale, SaleItem
from .services import create_sale, receive_sale, cancel_sale


class ItemInput(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=1000000)
    unit_price = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)


class SaleInput(serializers.Serializer):
    idempotency_key = serializers.UUIDField()
    channel = serializers.ChoiceField(choices=Sale.Channel.choices)
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    discount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0, default=0)
    platform_fee = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0, default=0)
    shipping_cost = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0, default=0)
    items = ItemInput(many=True, allow_empty=False)


class ItemOutput(serializers.ModelSerializer):
    class Meta:
        model = SaleItem
        fields = ["id", "product", "product_name", "quantity", "unit_price", "unit_cost", "cost_total"]


class SaleSerializer(serializers.ModelSerializer):
    items = ItemOutput(many=True, read_only=True)

    class Meta:
        model = Sale
        exclude = ["request_hash"]


class SaleViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Sale.objects.prefetch_related("items").all()
    serializer_class = SaleSerializer
    filterset_fields = ["channel", "status"]

    @extend_schema(request=SaleInput, responses={201: SaleSerializer})
    def create(self, request):
        if not request.user.has_perm("inventory.add_movement"):
            raise PermissionDenied("Sem permissão para baixar estoque.")
        serializer = SaleInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        sale = create_sale(data=serializer.validated_data, actor=request.user)
        return Response(SaleSerializer(sale).data, status=201)

    def _change_permission(self):
        if not self.request.user.has_perms(
            ["sales.change_sale", "inventory.add_movement", "finance.add_cashentry"]
        ):
            raise PermissionDenied("Sem permissão para movimentar venda, estoque e caixa.")

    @extend_schema(request=None, responses=SaleSerializer)
    @action(detail=True, methods=["post"])
    def receive(self, request, pk=None):
        self._change_permission()
        return Response(SaleSerializer(receive_sale(sale_id=self.get_object().id, actor=request.user)).data)

    @extend_schema(request=None, responses=SaleSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        self._change_permission()
        return Response(SaleSerializer(cancel_sale(sale_id=self.get_object().id, actor=request.user)).data)

    # ---------- vendas do Mercado Livre, importadas sob comando do dono (spec 015) ----------

    def _import_permission(self):
        if not self.request.user.has_perms(["inventory.add_movement", "integrations.view_marketplaceaccount"]):
            raise PermissionDenied("Sem permissão para importar vendas e baixar estoque.")

    @staticmethod
    def _integracao(chamada):
        """Erro do marketplace vira 400 legível, não 500."""
        from django.core.exceptions import ValidationError
        from apps.integrations.base import IntegrationError

        try:
            return chamada()
        except IntegrationError as exc:
            raise ValidationError({"integration": str(exc)}) from exc

    @extend_schema(
        parameters=[OpenApiParameter("days", int, required=False, description="Últimos N dias (1 a 90)")],
        responses=inline_serializer(
            name="MlOrdersPreview", fields={"pedidos": serializers.ListField(child=serializers.DictField())}
        ),
    )
    @action(detail=False, methods=["get"], url_path="ml-preview")
    def ml_preview(self, request):
        """Pedidos do Mercado Livre e a situação de cada um na loja. Só leitura."""
        from apps.integrations.meli.pedidos import previa

        self._import_permission()
        try:
            dias = max(1, min(int(request.query_params.get("days") or 30), 90))
        except ValueError:
            raise serializers.ValidationError({"days": "Informe um número de dias."})
        return Response({"pedidos": self._integracao(lambda: previa(dias))})

    @extend_schema(
        request=inline_serializer(
            name="MlOrdersImport",
            fields={"order_ids": serializers.ListField(child=serializers.CharField(max_length=40))},
        ),
        responses=inline_serializer(
            name="MlOrdersImported",
            fields={
                "importadas": serializers.ListField(child=serializers.CharField()),
                "canceladas": serializers.ListField(child=serializers.CharField()),
                "ignoradas": serializers.ListField(child=serializers.DictField()),
                "falhas": serializers.ListField(child=serializers.DictField()),
            },
        ),
    )
    @action(detail=False, methods=["post"], url_path="ml-import")
    def ml_import(self, request):
        """Cria as vendas dos pedidos escolhidos e cancela as dos pedidos cancelados."""
        from apps.integrations.meli.pedidos import importar

        self._import_permission()
        if not request.user.has_perms(["sales.change_sale", "finance.add_cashentry"]):
            raise PermissionDenied("Sem permissão para cancelar vendas importadas.")
        ids = request.data.get("order_ids")
        if not isinstance(ids, list) or not ids or len(ids) > 200:
            raise serializers.ValidationError({"order_ids": "Escolha de 1 a 200 pedidos."})
        if not all(str(i).isdigit() and len(str(i)) <= 40 for i in ids):
            raise serializers.ValidationError({"order_ids": "Código de pedido inválido."})
        return Response(self._integracao(lambda: importar(ids, actor=request.user)))
