from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from apps.supplies.domain.pricing import normalize_material
from apps.supplies.models import Supply, SupplyCategory, SupplyMovement, SupplyReceipt, SupplyStock
from apps.supplies.services import adjust_supply_stock


class SupplyCategorySerializer(serializers.ModelSerializer):
    supplies_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = SupplyCategory
        fields = ["id", "name", "is_filament", "active", "supplies_count", "created_at", "updated_at"]
        read_only_fields = ["id", "supplies_count", "created_at", "updated_at"]

    def validate_name(self, value):
        name = " ".join(value.split())
        if not name:
            raise serializers.ValidationError("Informe o nome da categoria.")
        outras = SupplyCategory.objects.all()
        if self.instance:
            outras = outras.exclude(pk=self.instance.pk)
        # casefold no Python: o iexact do SQLite não ignora maiúscula acentuada (Ô x ô)
        if any(nome.casefold() == name.casefold() for nome in outras.values_list("name", flat=True)):
            raise serializers.ValidationError("Já existe uma categoria de insumo com este nome.")
        return name

    def validate(self, attrs):
        flag = attrs.get("is_filament")
        if self.instance and flag is not None and flag != self.instance.is_filament and self.instance.supplies.exists():
            raise serializers.ValidationError(
                {"is_filament": "A categoria já tem insumos: não dá para mudar se ela é de filamento."}
            )
        return attrs


class SupplySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_is_filament = serializers.BooleanField(source="category.is_filament", read_only=True)
    price_per_gram = serializers.SerializerMethodField()
    price_per_kg = serializers.SerializerMethodField()
    # saldo atual (rolos ou unidades); muda só por compra, baixa e ajuste
    quantity = serializers.IntegerField(source="stock.quantity", read_only=True, default=0)

    class Meta:
        model = Supply
        fields = [
            "id", "category", "category_name", "category_is_filament", "name", "unit", "notes", "active",
            "material", "color", "roll_weight_g", "roll_price", "price_per_gram", "price_per_kg", "quantity",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        supply = super().create(validated_data)
        SupplyStock.objects.get_or_create(supply=supply)
        return supply

    def _format(self, value, places):
        return None if value is None else f"{value.quantize(Decimal(1).scaleb(-places))}"

    def get_price_per_gram(self, supply) -> str | None:
        return self._format(supply.price_per_gram, 6)

    def get_price_per_kg(self, supply) -> str | None:
        return self._format(supply.price_per_kg, 2)

    def validate(self, attrs):
        instance = self.instance
        category = attrs.get("category", getattr(instance, "category", None))
        if category is None:
            raise serializers.ValidationError({"category": "Escolha a categoria do insumo."})
        if instance and category.pk != instance.category_id:
            if category.is_filament != instance.category.is_filament:
                raise serializers.ValidationError(
                    {"category": "Só dá para trocar entre categorias do mesmo tipo (filamento ou não)."}
                )
        if (not instance or category.pk != instance.category_id) and not category.active:
            raise serializers.ValidationError({"category": "Esta categoria está inativa."})

        def value(field):
            return attrs[field] if field in attrs else getattr(instance, field, None)

        name = " ".join(str(value("name") or "").split())
        if not name:
            raise serializers.ValidationError({"name": "Informe o nome do insumo."})
        attrs["name"] = name
        colegas = Supply.objects.filter(category=category)
        if instance:
            colegas = colegas.exclude(pk=instance.pk)
        if any(nome.casefold() == name.casefold() for nome in colegas.values_list("name", flat=True)):
            raise serializers.ValidationError({"name": "Já existe um insumo com este nome nesta categoria."})

        filament_fields = ("material", "color", "roll_weight_g", "roll_price")
        if category.is_filament:
            errors = {}
            material = normalize_material(value("material") or "")
            color = " ".join(str(value("color") or "").split())
            if not material:
                errors["material"] = "Informe o material (PLA, PETG, ...)."
            if not color:
                errors["color"] = "Informe a cor."
            if not value("roll_weight_g"):
                errors["roll_weight_g"] = "Informe o peso do rolo em gramas."
            if value("roll_price") is None:
                errors["roll_price"] = "Informe o preço do rolo."
            if errors:
                raise serializers.ValidationError(errors)
            attrs["material"], attrs["color"] = material, color
        else:
            sobra = {f: "Só vale para filamento." for f in filament_fields if attrs.get(f) not in (None, "")}
            if sobra:
                raise serializers.ValidationError(sobra)
        return attrs



class SupplyReceiptInput(serializers.Serializer):
    idempotency_key = serializers.UUIDField()
    supply_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=1000000)
    unit_cost = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    occurred_on = serializers.DateField()
    supplier = serializers.CharField(max_length=200, allow_blank=True, default="")
    reference = serializers.CharField(max_length=100, allow_blank=True, default="")
    notes = serializers.CharField(max_length=500, allow_blank=True, default="")

    def validate_occurred_on(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("A compra não pode ter data futura.")
        return value


class SupplyPaymentInput(serializers.Serializer):
    occurred_on = serializers.DateField()


class SupplyReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplyReceipt
        exclude = ["request_hash", "previous_roll_price"]


class SupplyMovementSerializer(serializers.ModelSerializer):
    supply_name = serializers.CharField(source="supply.name", read_only=True)

    class Meta:
        model = SupplyMovement
        fields = ["id", "supply", "supply_name", "delta", "balance_after", "reason", "receipt", "actor", "created_at"]
        read_only_fields = ["id", "balance_after", "receipt", "actor", "created_at"]

    def create(self, data):
        return adjust_supply_stock(
            supply_id=data["supply"].id,
            delta=data["delta"],
            reason=data["reason"],
            actor=self.context["request"].user,
        )
