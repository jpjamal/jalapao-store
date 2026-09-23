from django.db import transaction
from rest_framework import serializers, viewsets, mixins
from .models import Product, PrintingProfile
from apps.inventory.models import Stock


class PrintingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintingProfile
        exclude = ["id", "product"]


class ProductSerializer(serializers.ModelSerializer):
    printing = PrintingSerializer(required=False, allow_null=True)
    quantity = serializers.IntegerField(source="stock.quantity", read_only=True, default=0)

    class Meta:
        model = Product
        fields = [
            "id",
            "sku",
            "name",
            "kind",
            "description",
            "cost_price",
            "sale_price",
            "active",
            "printing",
            "quantity",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        kind = attrs.get("kind", getattr(self.instance, "kind", "resale"))
        profile = attrs.get("printing", getattr(self.instance, "printing", None))
        if kind == "printing" and not profile:
            raise serializers.ValidationError({"printing": "Preencha os parâmetros de impressão 3D."})
        if kind != "printing" and attrs.get("printing"):
            raise serializers.ValidationError({"printing": "Parâmetros 3D exigem tipo Impressão 3D."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        profile = validated_data.pop("printing", None)
        product = Product.objects.create(**validated_data)
        Stock.objects.create(product=product)
        if profile:
            self._profile(product, profile)
        return product

    def _profile(self, product, data):
        profile, _ = PrintingProfile.objects.update_or_create(product=product, defaults=data)
        product.cost_price, product.sale_price = profile.prices()
        product.save(update_fields=["cost_price", "sale_price", "updated_at"])

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = Product.objects.select_for_update().get(pk=instance.pk)
        profile = validated_data.pop("printing", None)
        instance = super().update(instance, validated_data)
        if instance.kind == "printing":
            self._profile(instance, profile or {})
        else:
            PrintingProfile.objects.filter(product=instance).delete()
        return instance


class ProductViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Product.objects.select_related("printing", "stock").all()
    serializer_class = ProductSerializer
    filterset_fields = ["kind", "active"]
    search_fields = ["name", "sku"]
