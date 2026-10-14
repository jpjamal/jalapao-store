from rest_framework import serializers

from apps.sales.models import Sale, SaleItem, SaleLabel
from apps.supplies.models import SaleSupply


class ItemInput(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=1000000)
    unit_price = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)


class SaleSupplyInput(serializers.Serializer):
    """Insumo usado na venda (spec 024, etapa 3)."""

    supply_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=1000000)


def validate_zpl(value: str) -> str:
    if "\x00" in value:
        raise serializers.ValidationError("O ZPL contém um caractere inválido.")
    upper = value.upper()
    if "^XA" not in upper or "^XZ" not in upper:
        raise serializers.ValidationError("O conteúdo não parece uma etiqueta ZPL completa (^XA ... ^XZ).")
    return value


class LabelFields(serializers.Serializer):
    zpl = serializers.CharField(
        max_length=5_000_000,
        trim_whitespace=False,
        validators=[validate_zpl],
        required=False,
        allow_blank=False,
        write_only=True,
    )
    label_filename = serializers.CharField(max_length=255, required=False, allow_blank=True, write_only=True)
    label_order_id = serializers.CharField(max_length=100, required=False, allow_blank=True, write_only=True)
    label_name = serializers.CharField(max_length=200, required=False, allow_blank=True, write_only=True)
    label_city = serializers.CharField(max_length=120, required=False, allow_blank=True, write_only=True)
    label_state = serializers.CharField(max_length=60, required=False, allow_blank=True, write_only=True)


class SaleInput(LabelFields):
    idempotency_key = serializers.UUIDField()
    channel = serializers.ChoiceField(choices=Sale.Channel.choices)
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    discount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0, default=0)
    platform_fee = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0, default=0)
    shipping_cost = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0, default=0)
    items = ItemInput(many=True, allow_empty=False)
    supplies = SaleSupplyInput(many=True, required=False, default=list)

    def validate(self, attrs):
        label_fields = ("label_filename", "label_order_id", "label_name", "label_city", "label_state")
        if not attrs.get("zpl") and any(attrs.get(field) for field in label_fields):
            raise serializers.ValidationError({"zpl": "Adicione o código ZPL antes dos dados da etiqueta."})
        return attrs


class SaleLabelInput(serializers.Serializer):
    zpl = serializers.CharField(
        max_length=5_000_000,
        trim_whitespace=False,
        validators=[validate_zpl],
    )
    source_name = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    order_id = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    recipient_name = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    recipient_city = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    recipient_state = serializers.CharField(max_length=60, required=False, allow_blank=True, default="")


class SaleLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleLabel
        fields = [
            "zpl",
            "source_name",
            "order_id",
            "recipient_name",
            "recipient_city",
            "recipient_state",
            "created_at",
            "updated_at",
        ]


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
    has_label = serializers.SerializerMethodField()
    label_order_id = serializers.SerializerMethodField()
    label_filename = serializers.SerializerMethodField()

    @staticmethod
    def _label(obj):
        try:
            return obj.label
        except SaleLabel.DoesNotExist:
            return None

    def get_has_label(self, obj) -> bool:
        return self._label(obj) is not None

    def get_label_order_id(self, obj) -> str:
        label = self._label(obj)
        return label.order_id if label else ""

    def get_label_filename(self, obj) -> str:
        label = self._label(obj)
        return label.source_name if label else ""

    class Meta:
        model = Sale
        exclude = ["request_hash"]
