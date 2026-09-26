from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.inventory.api.serializers import MovementSerializer, PaymentInput, ReceiptInput, ReceiptSerializer
from apps.inventory.models import Movement, Receipt
from apps.inventory.services import create_receipt, pay_receipt


class MovementViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Movement.objects.select_related("product").all()
    serializer_class = MovementSerializer
    filterset_fields = ["product"]


class ReceiptViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Receipt.objects.all()
    serializer_class = ReceiptSerializer
    filterset_fields = ["product", "kind"]

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
