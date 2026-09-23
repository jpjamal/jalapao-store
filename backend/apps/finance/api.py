from rest_framework import serializers, viewsets, mixins
from .models import CashEntry


class CashSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashEntry
        fields = [
            "id",
            "direction",
            "amount",
            "description",
            "occurred_on",
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

    def create(self, data):
        return CashEntry.objects.create(**data, actor=self.context["request"].user)


class CashViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = CashEntry.objects.all()
    serializer_class = CashSerializer
    filterset_fields = ["direction"]
