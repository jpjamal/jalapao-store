from rest_framework import serializers, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from .models import Movement, Receipt
from .services import adjust_stock, create_receipt, pay_receipt


class MovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    unit_cost = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=0, required=False, write_only=True
    )

    class Meta:
        model = Movement
        fields = [
            "id",
            "product",
            "product_name",
            "delta",
            "reason",
            "balance_after",
            "sale",
            "actor",
            "created_at",
            "unit_cost",
            "receipt",
            "value_delta",
            "value_after",
        ]
        read_only_fields = [
            "id",
            "balance_after",
            "sale",
            "actor",
            "created_at",
            "receipt",
            "value_delta",
            "value_after",
        ]

    def create(self, data):
        return adjust_stock(
            product_id=data["product"].id,
            delta=data["delta"],
            reason=data["reason"],
            actor=self.context["request"].user,
            unit_cost=data.get("unit_cost"),
        )


class MovementViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Movement.objects.select_related("product").all()
    serializer_class = MovementSerializer
    filterset_fields = ["product"]


class ReceiptInput(serializers.Serializer):
    idempotency_key = serializers.UUIDField()
    product_id = serializers.UUIDField()
    kind = serializers.ChoiceField(choices=Receipt.Kind.choices)
    quantity = serializers.IntegerField(min_value=1, max_value=1000000)
    unit_cost = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    occurred_on = serializers.DateField()
    supplier = serializers.CharField(max_length=200, allow_blank=True, default="")
    reference = serializers.CharField(max_length=100, allow_blank=True, default="")
    notes = serializers.CharField(max_length=500, allow_blank=True, default="")

    def validate_occurred_on(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("Entrada não pode ter data futura.")
        return value


class PaymentInput(serializers.Serializer):
    occurred_on = serializers.DateField()


class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        exclude = ["request_hash"]


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
