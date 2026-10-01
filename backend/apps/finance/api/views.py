from decimal import Decimal

from django.db.models import Count, Q, Sum
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.finance.api.filters import CashFilter
from apps.finance.api.serializers import CashCategorySerializer, CashSerializer
from apps.finance.models import CashCategory, CashEntry


class CashCategoryViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Sem DELETE: categoria sai de uso desativando (`active`). As do sistema são só de leitura."""

    queryset = CashCategory.objects.annotate(entries_count=Count("entries")).order_by("name", "id")
    serializer_class = CashCategorySerializer
    filterset_fields = ["direction", "active", "counts_in_result"]
    search_fields = ["name"]
    ordering_fields = ["name", "direction", "entries_count", "counts_in_result", "active"]
    ordering_text_fields = ["name"]

    def get_queryset(self):
        queryset = super().get_queryset()
        system = self.request.query_params.get("system")
        if system in ("true", "false"):
            queryset = queryset.filter(system_key__isnull=(system == "false"))
        return queryset


class CashViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    queryset = CashEntry.objects.select_related("category").all()
    serializer_class = CashSerializer
    filterset_class = CashFilter
    search_fields = ["description", "category__name"]
    ordering_fields = ["occurred_on", "created_at", "amount", "description", "category__name", "direction"]
    ordering_text_fields = ["description", "category__name"]
    # só PATCH: reclassificar é a única edição permitida num lançamento
    http_method_names = ["get", "post", "patch", "head", "options"]

    @extend_schema(
        responses=inline_serializer(
            name="CashSummary",
            many=True,
            fields={
                "category": serializers.UUIDField(),
                "category_name": serializers.CharField(),
                "is_system": serializers.BooleanField(),
                "counts_in_result": serializers.BooleanField(),
                "entries": serializers.IntegerField(),
                "in_total": serializers.CharField(),
                "out_total": serializers.CharField(),
            },
        )
    )
    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Entradas e saídas somadas por categoria, de todos os lançamentos."""
        rows = (
            CashEntry.objects.values("category", "category__name", "category__system_key", "category__counts_in_result")
            .annotate(
                entries=Count("id"),
                in_total=Sum("amount", filter=Q(direction="in")),
                out_total=Sum("amount", filter=Q(direction="out")),
            )
            .order_by("category__name")
        )
        return Response(
            [
                {
                    "category": row["category"],
                    "category_name": row["category__name"],
                    "is_system": row["category__system_key"] is not None,
                    "counts_in_result": row["category__counts_in_result"],
                    "entries": row["entries"],
                    # sempre com duas casas, qualquer que seja o banco
                    "in_total": f"{Decimal(row['in_total'] or 0):.2f}",
                    "out_total": f"{Decimal(row['out_total'] or 0):.2f}",
                }
                for row in rows
            ]
        )
