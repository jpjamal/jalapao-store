from rest_framework import serializers

from apps.sales.models import Sale, SaleItem
from apps.supplies.models import SaleSupply


class ItemInput(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=1000000)
    unit_price = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)


class SaleSupplyInput(serializers.Serializer):
    """Insumo usado na venda (spec 024, etapa 3)."""

    supply_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=1000000)


class SaleInput(serializers.Serializer):
    idempotency_key = serializers.UUIDField()
    channel = serializers.ChoiceField(choices=Sale.Channel.choices)
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    discount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0, default=0)
    platform_fee = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0, default=0)
    shipping_cost = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0, default=0)
    items = ItemInput(many=True, allow_empty=False)
    supplies = SaleSupplyInput(many=True, required=False, default=list)


class ItemOutput(serializers.ModelSerializer):
    class Meta:
        model = SaleItem
        fields = ["id", "product", "product_name", "quantity", "unit_price", "unit_cost", "cost_total"]


class StrictInput(serializers.Serializer):
    def to_internal_value(self, data):
        if isinstance(data, dict) and set(data) - set(self.fields):
            raise serializers.ValidationError(
                {"non_field_errors": ["Há campos que não podem ser alterados nesta operação."]}
            )
        return super().to_internal_value(data)


class ItemPriceInput(StrictInput):
    id = serializers.UUIDField()
    unit_price = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)


class SaleEditInput(StrictInput):
    request_key = serializers.UUIDField()
    expected_updated_at = serializers.DateTimeField()
    channel = serializers.ChoiceField(choices=Sale.Channel.choices, required=False)
    reference = serializers.CharField(max_length=100, allow_blank=True, required=False)
    discount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0, required=False)
    platform_fee = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0, required=False)
    shipping_cost = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0, required=False)
    items = ItemPriceInput(many=True, allow_empty=False, required=False)


class SaleSupplyOutput(serializers.ModelSerializer):
    # quanto faltou de saldo na hora da venda (0 quando baixou tudo o que foi pedido)
    shortfall = serializers.SerializerMethodField()

    class Meta:
        model = SaleSupply
        fields = ["supply", "supply_name", "requested", "taken", "shortfall"]

    def get_shortfall(self, line) -> int:
        return line.requested - line.taken


class SaleSerializer(serializers.ModelSerializer):
    items = ItemOutput(many=True, read_only=True)
    supplies = SaleSupplyOutput(source="supply_lines", many=True, read_only=True)

    class Meta:
        model = Sale
        exclude = ["request_hash"]
