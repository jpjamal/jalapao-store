"""Custo médio ponderado do estoque (spec 002)."""

from decimal import Decimal

from django.core.exceptions import ValidationError

from apps.common.domain.money import money

VALOR_MAXIMO = Decimal("999999999999.99")


def check_value(value: Decimal) -> None:
    """Valor dentro do que o banco guarda (14 dígitos, 2 decimais) e nunca negativo."""
    if value < 0 or value > VALOR_MAXIMO:
        raise ValidationError({"unit_cost": "Valor fora do limite suportado."})


def outgoing_value(*, available: int, value: Decimal, quantity: int) -> Decimal:
    """Valor que sai do estoque ao retirar `quantity` unidades, pelo custo médio. Retirar tudo
    leva o valor inteiro, para não sobrar centavo de arredondamento."""
    if quantity > available:
        raise ValidationError({"quantity": f"Estoque insuficiente. Disponível: {available}."})
    return value if quantity == available else money(value * quantity / available)
