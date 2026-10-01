"""Filtros das listagens de insumos (spec 027): saldo, pagamento, tipo de movimento e período."""

import django_filters

from apps.common.filters import range_filterset
from apps.supplies.models import Supply, SupplyMovement, SupplyReceipt


class SupplyFilter(django_filters.FilterSet):
    # `in_stock=true`: com saldo; `in_stock=false`: sem saldo (inclusive insumo que nunca teve compra)
    in_stock = django_filters.BooleanFilter(method="filter_in_stock")

    class Meta:
        model = Supply
        fields = ["category", "active", "material"]

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__quantity__gt=0)
        return queryset.exclude(stock__quantity__gt=0)


def _paid(queryset, name, value):
    """`paid=true`: já paga. `paid=false`: confirmada e ainda a pagar."""
    if value:
        return queryset.filter(paid_at__isnull=False)
    return queryset.filter(status="confirmed", paid_at__isnull=True)


def _direction(queryset, name, value):
    return queryset.filter(delta__gt=0) if value == "in" else queryset.filter(delta__lt=0)


SupplyReceiptFilter = range_filterset(
    SupplyReceipt,
    date_field="occurred_on",
    fields=["supply", "status"],
    extra={"paid": django_filters.BooleanFilter(method=_paid)},
)

SupplyMovementFilter = range_filterset(
    SupplyMovement,
    date_field="created_at",
    datetime_field=True,
    fields=["supply"],
    extra={"direction": django_filters.ChoiceFilter(choices=[("in", "Entrada"), ("out", "Saída")], method=_direction)},
)
