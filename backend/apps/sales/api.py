from rest_framework import serializers, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
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
        fields = ["id", "product", "product_name", "quantity", "unit_price", "unit_cost"]


class SaleSerializer(serializers.ModelSerializer):
    items = ItemOutput(many=True, read_only=True)

    class Meta:
        model = Sale
        exclude = ["request_hash"]


class SaleViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Sale.objects.prefetch_related("items").all()
    serializer_class = SaleSerializer
    filterset_fields = ["channel", "status"]

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

    @action(detail=True, methods=["post"])
    def receive(self, request, pk=None):
        self._change_permission()
        return Response(SaleSerializer(receive_sale(sale_id=self.get_object().id, actor=request.user)).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        self._change_permission()
        return Response(SaleSerializer(cancel_sale(sale_id=self.get_object().id, actor=request.user)).data)
