from decimal import Decimal, ROUND_HALF_UP


def money(value):
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


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
):
    duration = Decimal(hours) + Decimal(minutes) / 60
    filament = Decimal(filament_price_kg) * Decimal(weight_g) / 1000
    energy = Decimal(power_w) * duration * Decimal(energy_price_kwh) / 1000
    total = filament + energy + Decimal(labor_cost) + Decimal(fixed_cost)
    return money(total), money(total * (1 + Decimal(markup_percent) / 100))
