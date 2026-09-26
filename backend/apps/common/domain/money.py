"""Dinheiro: todo valor da loja é em reais, com duas casas e arredondamento comercial."""

from decimal import ROUND_HALF_UP, Decimal

CENTAVO = Decimal("0.01")


def money(value) -> Decimal:
    """Arredonda para centavos (meio para cima), como no caixa."""
    return Decimal(value).quantize(CENTAVO, rounding=ROUND_HALF_UP)
