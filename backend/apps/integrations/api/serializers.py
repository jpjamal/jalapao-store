from rest_framework import serializers

from apps.integrations.models import Listing, MarketplaceAccount


class AccountSerializer(serializers.ModelSerializer):
    channel_label = serializers.CharField(source="get_channel_display", read_only=True)
    token_valido = serializers.BooleanField(read_only=True)
    authorization_days_left = serializers.IntegerField(
        source="dias_ate_expirar_autorizacao", read_only=True, allow_null=True
    )

    class Meta:
        model = MarketplaceAccount
        fields = [
            "id",
            "channel",
            "channel_label",
            "external_id",
            "name",
            "active",
            "token_valido",
            "authorization_expires_at",
            "authorization_days_left",
            "last_synced_at",
            "last_error",
            "created_at",
        ]
        read_only_fields = fields


class ListingSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    local_stock = serializers.IntegerField(source="product.stock.quantity", read_only=True)

    class Meta:
        model = Listing
        fields = [
            "id",
            "marketplace",
            "seller_id",
            "item_id",
            "title",
            "product",
            "product_name",
            "product_sku",
            "local_stock",
            "remote_stock",
            "sync_enabled",
            "stock_pushed_at",
        ]
        read_only_fields = [
            "id",
            "marketplace",
            "seller_id",
            "item_id",
            "title",
            "product_name",
            "product_sku",
            "local_stock",
            "remote_stock",
            "stock_pushed_at",
        ]

    def validate(self, attrs):
        if self.instance and self.instance.sync_enabled and attrs.get("product", self.instance.product) != self.instance.product:
            raise serializers.ValidationError({"product": "Desative a sincronia antes de trocar o produto."})
        return attrs

    def update(self, instance, validated_data):
        if (validated_data.get("sync_enabled") is True and not instance.sync_enabled) or (
            "product" in validated_data and validated_data["product"] != instance.product
        ):
            instance.last_pushed_version = None
        return super().update(instance, validated_data)
