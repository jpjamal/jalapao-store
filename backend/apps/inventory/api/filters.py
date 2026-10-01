"""Filtros das listagens do estoque (spec 027): período, tipo de movimento e pagamento."""

import django_filters

from apps.common.filters import range_filterset
from apps.inventory.models import Movement, Receipt


def _direction(queryset, name, value):
    return queryset.filter(delta__gt=0) if value == "in" else queryset.filter(delta__lt=0)


def _paid(queryset, name, value):
    """`paid=true`: já paga. `paid=false`: compra confirmada ainda a pagar (produção nunca é paga)."""
    if value:
        return queryset.filter(paid_at__isnull=False)
    return queryset.filter(kind="purchase", status="confirmed", paid_at__isnull=True)


MovementFilter = range_filterset(
    Movement,
    date_field="created_at",
    datetime_field=True,
    fields=["product"],
    extra={"direction": django_filters.ChoiceFilter(choices=[("in", "Entrada"), ("out", "Saída")], method=_direction)},
)

ReceiptFilter = range_filterset(
    Receipt,
    date_field="occurred_on",
    fields=["product", "kind", "status"],
    extra={"paid": django_filters.BooleanFilter(method=_paid)},
)
