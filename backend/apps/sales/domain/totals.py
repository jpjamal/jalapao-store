"""Valores da venda: bruto dos itens e líquido depois de desconto, taxa e frete."""

from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError

from apps.common.domain.money import money


@dataclass(frozen=True)
class SaleTotals:
    gross: Decimal
    net: Decimal


def sale_totals(*, items, discount: Decimal, fee: Decimal, shipping: Decimal) -> SaleTotals:
    """`items`: linhas com `unit_price` e `quantity`. Desconto, taxa e frete não podem
    levar o líquido abaixo de zero, nem o desconto passar do bruto."""
    gross = money(sum(row["unit_price"] * row["quantity"] for row in items))
    net = money(gross - discount - fee - shipping)
    if discount > gross or net < 0:
        raise ValidationError({"discount": "Descontos, taxas e frete não podem superar o valor bruto."})
    return SaleTotals(gross=gross, net=net)
