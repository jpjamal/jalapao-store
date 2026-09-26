from rest_framework import serializers

from apps.sales.models import Sale, SaleItem


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
