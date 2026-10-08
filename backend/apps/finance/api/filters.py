"""Filtros da lista do Caixa (spec 027): período e origem do lançamento."""

import django_filters

from apps.common.filters import range_filterset
from apps.finance.domain.categories import ORIGINS
from apps.finance.models import CashEntry

# a origem não é uma coluna: vem de qual ligação o lançamento tem. Cada origem, como condições do banco.
_ORIGIN_LOOKUPS = {
    "sale": {"sale__isnull": False, "direction": "in", "sale_revision__isnull": True},
    "sale_refund": {"sale__isnull": False, "direction": "out", "sale_revision__isnull": True},
    "sale_adjustment": {"sale_revision__isnull": False},
    "purchase": {"sale__isnull": True, "receipt__isnull": False},
    "purchase_refund": {"refund_of_receipt__isnull": False},
    "supply": {"supply_receipt__isnull": False},
    "supply_refund": {"refund_of_supply_receipt__isnull": False},
    "manual": {
        "sale__isnull": True,
        "receipt__isnull": True,
        "refund_of_receipt__isnull": True,
        "supply_receipt__isnull": True,
        "refund_of_supply_receipt__isnull": True,
    },
}


def _origin(queryset, name, value):
    return queryset.filter(**_ORIGIN_LOOKUPS[value])


CashFilter = range_filterset(
    CashEntry,
    date_field="occurred_on",
    fields=["direction", "category"],
    extra={"origin": django_filters.ChoiceFilter(choices=list(ORIGINS.items()), method=_origin)},
)
