from django.db.models import Count
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.supplies.api.filters import SupplyFilter, SupplyMovementFilter, SupplyReceiptFilter
from apps.supplies.api.serializers import (
    SupplyCategorySerializer,
    SupplyMovementSerializer,
    SupplyPaymentInput,
    SupplyReceiptInput,
    SupplyReceiptSerializer,
    SupplySerializer,
)
from apps.supplies.domain.pricing import MATERIAIS
from apps.supplies.models import Supply, SupplyCategory, SupplyMovement, SupplyReceipt
from apps.supplies.services import cancel_supply_receipt, create_supply_receipt, pay_supply_receipt


class SupplyCategoryViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Sem DELETE: categoria sai de uso desativando (`active`)."""

    queryset = SupplyCategory.objects.annotate(supplies_count=Count("supplies")).order_by("name", "id")
    serializer_class = SupplyCategorySerializer
    filterset_fields = ["active", "is_filament"]
    search_fields = ["name"]
    ordering_fields = ["name", "supplies_count", "is_filament", "counts_as_expense", "active"]
    ordering_text_fields = ["name"]


class SupplyViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Sem DELETE: insumo sai de uso desativando (`active`)."""

    queryset = Supply.objects.select_related("category", "stock").all()
    serializer_class = SupplySerializer
    filterset_class = SupplyFilter
    search_fields = ["name", "color", "material", "category__name"]
    ordering_fields = [
        "name", "category__name", "stock__quantity", "roll_price", "material", "color", "unit", "active",
    ]
    ordering_text_fields = ["name", "category__name", "material", "color", "unit"]
    ordering_zero_fields = ["stock__quantity"]

    @extend_schema(
        responses=inline_serializer(
            name="SupplyMaterials", fields={"results": serializers.ListField(child=serializers.CharField())}
        )
    )
    @action(detail=False, methods=["get"])
    def materials(self, request):
        """Sugestões de material para o cadastro de filamento; aceita outro valor digitado."""
        return Response({"results": MATERIAIS})


class SupplyReceiptViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = SupplyReceipt.objects.all()
    serializer_class = SupplyReceiptSerializer
    filterset_class = SupplyReceiptFilter
    search_fields = ["supply_name", "supplier", "reference", "notes"]
    ordering_fields = ["occurred_on", "created_at", "supply_name", "quantity", "unit_cost", "total", "status", "paid_at"]
    ordering_text_fields = ["supply_name"]

    @extend_schema(request=SupplyReceiptInput, responses={201: SupplyReceiptSerializer})
    def create(self, request):
        if not request.user.has_perm("supplies.add_supplymovement"):
            raise PermissionDenied("Sem permissão para movimentar o estoque de insumos.")
        serializer = SupplyReceiptInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        receipt = create_supply_receipt(data=serializer.validated_data, actor=request.user)
        return Response(SupplyReceiptSerializer(receipt).data, status=201)

    @extend_schema(request=SupplyPaymentInput, responses=SupplyReceiptSerializer)
    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        if not request.user.has_perms(["supplies.change_supplyreceipt", "finance.add_cashentry"]):
            raise PermissionDenied("Sem permissão para pagar compras de insumo.")
        serializer = SupplyPaymentInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        receipt = pay_supply_receipt(
            receipt_id=self.get_object().id, actor=request.user, **serializer.validated_data
        )
        return Response(SupplyReceiptSerializer(receipt).data)

    @extend_schema(request=None, responses=SupplyReceiptSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        if not request.user.has_perms(
            ["supplies.change_supplyreceipt", "supplies.add_supplymovement", "finance.add_cashentry"]
        ):
            raise PermissionDenied("Sem permissão para cancelar compras de insumo, estoque e caixa.")
        receipt = cancel_supply_receipt(receipt_id=self.get_object().id, actor=request.user)
        return Response(SupplyReceiptSerializer(receipt).data)


class SupplyMovementViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Razão do saldo. Criar aqui é dar baixa ou ajustar (delta negativo ou positivo, com motivo)."""

    queryset = SupplyMovement.objects.select_related("supply").all()
    serializer_class = SupplyMovementSerializer
    filterset_class = SupplyMovementFilter
    search_fields = ["supply__name", "reason"]
    ordering_fields = ["created_at", "supply__name", "delta", "balance_after"]
    ordering_text_fields = ["supply__name"]
