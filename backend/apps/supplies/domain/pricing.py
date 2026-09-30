"""Preço do filamento por grama e por kg, e sugestões de material (spec 024).

O preço por grama **não é arredondado**: o dono guarda o preço e o peso do rolo, e só o total em
centavos é arredondado por quem usa esta conta.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError

MATERIAIS = ["PLA", "PLA+", "PETG", "ABS", "ASA", "TPU", "Seda", "Madeira"]


def price_per_gram(roll_price, roll_weight_g) -> Decimal:
    """`preço do rolo ÷ peso do rolo` (R$ 100,00 por 1.000 g = R$ 0,10 por grama)."""
    return Decimal(roll_price) / Decimal(roll_weight_g)


def price_per_kg(roll_price, roll_weight_g) -> Decimal:
    return price_per_gram(roll_price, roll_weight_g) * 1000


def normalize_material(value: str) -> str:
    """Tira espaços e, se for uma das sugestões, usa a grafia dela ("pla" vira "PLA")."""
    text = " ".join((value or "").split())
    for known in MATERIAIS:
        if text.casefold() == known.casefold():
            return known
    return text


VALOR_MAXIMO = Decimal("999999999999.99")


def check_amount(value) -> None:
    """Valor em reais dentro do que o banco guarda e nunca negativo."""
    if value < 0 or value > VALOR_MAXIMO:
        raise ValidationError({"unit_cost": "Valor fora do limite suportado."})
