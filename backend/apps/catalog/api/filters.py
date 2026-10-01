"""Filtros das listagens do catálogo (spec 027)."""

import django_filters

from apps.catalog.models import Product


class ProductFilter(django_filters.FilterSet):
    # `in_stock=true`: com saldo; `in_stock=false`: sem saldo (inclusive produto que nunca teve estoque)
    in_stock = django_filters.BooleanFilter(method="filter_in_stock")

    class Meta:
        model = Product
        fields = ["category", "active"]

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__quantity__gt=0)
        return queryset.exclude(stock__quantity__gt=0)
