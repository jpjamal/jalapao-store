from django.utils import timezone
from rest_framework import serializers

from apps.inventory.models import Movement, Receipt
from apps.inventory.services import adjust_stock
from apps.supplies.models import ProductionSupply


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
    # produção: dar baixa no filamento e nos componentes da peça (spec 041). Desligar serve para lançar
    # peças que já estavam prontas antes, cujos insumos já saíram do estoque.
    consume_supplies = serializers.BooleanField(default=True)

    def validate_occurred_on(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("Entrada não pode ter data futura.")
        return value


class PaymentInput(serializers.Serializer):
    occurred_on = serializers.DateField()


class ProductionSupplyOutput(serializers.ModelSerializer):
    """Insumo que a produção tirou do estoque (spec 041)."""

    class Meta:
        model = ProductionSupply
        fields = ["supply", "supply_name", "unit", "requested", "taken"]


class ReceiptSerializer(serializers.ModelSerializer):
    supply_lines = ProductionSupplyOutput(many=True, read_only=True)

    class Meta:
        model = Receipt
        exclude = ["request_hash"]
