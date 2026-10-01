from rest_framework import serializers

from apps.finance.domain.categories import direction_fits
from apps.finance.models import CashCategory, CashEntry


class CashCategorySerializer(serializers.ModelSerializer):
    is_system = serializers.BooleanField(read_only=True)
    entries_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = CashCategory
        fields = [
            "id", "name", "direction", "counts_in_result", "active", "is_system", "entries_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "is_system", "entries_count", "created_at", "updated_at"]

    def validate_name(self, value):
        name = " ".join(value.split())
        if not name:
            raise serializers.ValidationError("Informe o nome da categoria.")
        outras = CashCategory.objects.all()
        if self.instance:
            outras = outras.exclude(pk=self.instance.pk)
        # casefold no Python: o iexact do SQLite não ignora maiúscula acentuada (Ô x ô)
        if any(nome.casefold() == name.casefold() for nome in outras.values_list("name", flat=True)):
            raise serializers.ValidationError("Já existe uma categoria do Caixa com este nome.")
        return name

    def validate(self, attrs):
        if self.instance and self.instance.is_system:
            raise serializers.ValidationError("Categoria do sistema não pode ser alterada.")
        direction = attrs.get("direction")
        if self.instance and direction and direction != self.instance.direction and self.instance.entries.exists():
            raise serializers.ValidationError(
                {"direction": "A categoria já tem lançamentos: não dá para mudar a direção dela."}
            )
        return attrs


class CashSerializer(serializers.ModelSerializer):
    """Lançamento do Caixa. Manual exige categoria; depois de criado, só a categoria do manual muda
    (reclassificar). Valor, data, descrição e direção são imutáveis: correção é por lançamento inverso."""

    category = serializers.PrimaryKeyRelatedField(queryset=CashCategory.objects.all(), required=False)
    category_name = serializers.CharField(source="category.name", read_only=True)
    origin = serializers.CharField(read_only=True)

    class Meta:
        model = CashEntry
        fields = [
            "id",
            "direction",
            "amount",
            "description",
            "occurred_on",
            "category",
            "category_name",
            "origin",
            "sale",
            "receipt",
            "actor",
            "created_at",
        ]
        read_only_fields = ["id", "sale", "receipt", "actor", "created_at"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Informe um valor maior que zero.")
        return value

    def validate(self, attrs):
        category = attrs.get("category")
        if self.instance:
            outros = set(attrs) - {"category"}
            if outros:
                raise serializers.ValidationError(
                    "Só a categoria pode ser alterada: para corrigir valor, data ou descrição, faça um lançamento inverso."
                )
            if self.instance.origin != "manual":
                raise serializers.ValidationError("Só lançamento manual pode ser reclassificado.")
            if category is None:
                raise serializers.ValidationError({"category": "Informe a categoria."})
            direction = self.instance.direction
        else:
            if category is None:
                raise serializers.ValidationError({"category": "Escolha a categoria do lançamento."})
            direction = attrs["direction"]
        if category.is_system:
            raise serializers.ValidationError({"category": "Esta categoria é do sistema e não pode ser escolhida."})
        if not category.active:
            raise serializers.ValidationError({"category": "Esta categoria está inativa."})
        if not direction_fits(category.direction, direction):
            raise serializers.ValidationError(
                {"category": "A categoria não combina com o tipo do lançamento (entrada ou saída)."}
            )
        return attrs

    def create(self, data):
        return CashEntry.objects.create(**data, actor=self.context["request"].user)

    def update(self, instance, data):
        instance.category = data["category"]
        instance.save(update_fields=["category", "updated_at"])
        return instance
