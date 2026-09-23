from rest_framework import serializers, viewsets, mixins
from .models import Movement
from .services import adjust_stock


class MovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

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
        ]
        read_only_fields = ["id", "balance_after", "sale", "actor", "created_at"]

    def create(self, data):
        return adjust_stock(
            product_id=data["product"].id,
            delta=data["delta"],
            reason=data["reason"],
            actor=self.context["request"].user,
        )


class MovementViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Movement.objects.select_related("product").all()
    serializer_class = MovementSerializer
    filterset_fields = ["product"]
