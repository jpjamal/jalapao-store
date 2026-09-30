"""Custo e preço sugerido de uma peça impressa em 3D."""

from decimal import Decimal

from apps.common.domain.money import money


def filament_cost(lines) -> Decimal:
    """Custo do filamento de uma peça multicolor (spec 024): soma, linha a linha, de
    `gramas × preço do rolo ÷ peso do rolo`, sem arredondar o preço por grama. Cada linha é uma
    tupla `(gramas, preço do rolo, peso do rolo em gramas)`; só o total final vira centavos."""
    return sum(
        (Decimal(grams) * Decimal(roll_price) / Decimal(roll_weight_g) for grams, roll_price, roll_weight_g in lines),
        Decimal(0),
    )


def printing_cost(
    *,
    filament_price_kg,
    weight_g,
    power_w,
    hours,
    minutes,
    energy_price_kwh,
    labor_cost,
    fixed_cost,
    markup_percent,
    filament_lines=None,
) -> tuple[Decimal, Decimal]:
    """Devolve (custo, preço sugerido): filamento + energia + mão de obra + fixos, e a margem.
    Com `filament_lines` (peça multicolor) o filamento é a soma das linhas; sem elas vale a conta
    de sempre, com o preço por kg e o peso total."""
    duration = Decimal(hours) + Decimal(minutes) / 60
    if filament_lines:
        filament = filament_cost(filament_lines)
    else:
        filament = Decimal(filament_price_kg) * Decimal(weight_g) / 1000
    energy = Decimal(power_w) * duration * Decimal(energy_price_kwh) / 1000
    total = filament + energy + Decimal(labor_cost) + Decimal(fixed_cost)
    return money(total), money(total * (1 + Decimal(markup_percent) / 100))
