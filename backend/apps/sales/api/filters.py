"""Filtros da lista de vendas (spec 027): período e recebimento."""

import django_filters

from apps.common.filters import range_filterset
from apps.sales.models import Sale


def _received(queryset, name, value):
    """`received=true`: já recebida. `received=false`: confirmada e ainda a receber."""
    if value:
        return queryset.filter(received_at__isnull=False)
    return queryset.filter(status="confirmed", received_at__isnull=True)


SaleFilter = range_filterset(
    Sale,
    date_field="created_at",
    datetime_field=True,
    fields=["channel", "status"],
    extra={"received": django_filters.BooleanFilter(method=_received)},
)
