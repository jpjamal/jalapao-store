from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.inventory.api.filters import MovementFilter, ReceiptFilter
from apps.inventory.api.serializers import MovementSerializer, PaymentInput, ReceiptInput, ReceiptSerializer
from apps.inventory.models import Movement, Receipt
from apps.inventory.services import cancel_receipt, create_receipt, pay_receipt


class MovementViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Movement.objects.select_related("product").all()
    serializer_class = MovementSerializer
    filterset_class = MovementFilter
    search_fields = ["product__name", "product__sku", "reason"]
    ordering_fields = ["created_at", "product__name", "delta", "balance_after", "value_delta"]
    ordering_text_fields = ["product__name"]


class ReceiptViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Receipt.objects.all()
    serializer_class = ReceiptSerializer
    filterset_class = ReceiptFilter
    search_fields = ["product_name", "supplier", "reference", "notes"]
    ordering_fields = [
        "occurred_on", "created_at", "product_name", "quantity", "unit_cost", "total", "kind", "status", "paid_at",
    ]
    ordering_text_fields = ["product_name"]

    @extend_schema(request=ReceiptInput, responses={201: ReceiptSerializer})
    def create(self, request):
        if not request.user.has_perm("inventory.add_movement"):
            raise PermissionDenied("Sem permissão para movimentar estoque.")
        serializer = ReceiptInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        receipt = create_receipt(data=serializer.validated_data, actor=request.user)
        return Response(ReceiptSerializer(receipt).data, status=201)

    @extend_schema(request=PaymentInput, responses=ReceiptSerializer)
    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        if not request.user.has_perms(["inventory.change_receipt", "finance.add_cashentry"]):
            raise PermissionDenied("Sem permissão para pagar compras.")
        serializer = PaymentInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        receipt = pay_receipt(
            receipt_id=self.get_object().id, actor=request.user, **serializer.validated_data
        )
        return Response(ReceiptSerializer(receipt).data)

    @extend_schema(request=None, responses=ReceiptSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        if not request.user.has_perms(["inventory.change_receipt", "inventory.add_movement", "finance.add_cashentry"]):
            raise PermissionDenied("Sem permissão para cancelar compras, estoque e caixa.")
        receipt = cancel_receipt(receipt_id=self.get_object().id, actor=request.user)
        return Response(ReceiptSerializer(receipt).data)
