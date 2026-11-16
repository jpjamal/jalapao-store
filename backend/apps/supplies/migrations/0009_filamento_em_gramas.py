"""Spec 041: filamento passa a ser contado em gramas, e nasce a categoria Componentes.

Para cada insumo de filamento, o saldo, a parte sem custo, o histórico de movimentos e as linhas de venda
que o usaram são multiplicados pelo peso do rolo: 2 rolos de 1.000 g viram 2.000 g. As compras continuam
em rolos (é como se compra), e o preço do rolo não muda. A unidade do insumo vira "g".

Componentes (LED, parafuso, cabo) é uma categoria nova que não conta como despesa na compra: o custo deles
entra no custo da peça 3D. Se já existir uma categoria com esse nome, ela é mantida como está."""

from decimal import ROUND_HALF_UP, Decimal

from django.db import migrations

PESO_PADRAO = Decimal(1000)


def _peso(supply):
    peso = supply.roll_weight_g or PESO_PADRAO
    return int(Decimal(peso).to_integral_value(rounding=ROUND_HALF_UP)) or 1000


def para_gramas(apps, schema_editor):
    Supply = apps.get_model("supplies", "Supply")
    SupplyStock = apps.get_model("supplies", "SupplyStock")
    SupplyMovement = apps.get_model("supplies", "SupplyMovement")
    SaleSupply = apps.get_model("supplies", "SaleSupply")
    for supply in Supply.objects.filter(category__is_filament=True):
        peso = _peso(supply)
        stock = SupplyStock.objects.filter(supply=supply).first()
        if stock:
            stock.quantity *= peso
            stock.uncosted *= peso
            stock.save(update_fields=["quantity", "uncosted"])
        for movement in SupplyMovement.objects.filter(supply=supply):
            movement.delta *= peso
            movement.balance_after *= peso
            movement.save(update_fields=["delta", "balance_after"])
        for line in SaleSupply.objects.filter(supply=supply):
            line.requested *= peso
            line.taken *= peso
            line.zero_cost_qty *= peso
            line.save(update_fields=["requested", "taken", "zero_cost_qty"])
        supply.unit = "g"
        supply.save(update_fields=["unit"])


def para_rolos(apps, schema_editor):
    Supply = apps.get_model("supplies", "Supply")
    SupplyStock = apps.get_model("supplies", "SupplyStock")
    SupplyMovement = apps.get_model("supplies", "SupplyMovement")
    SaleSupply = apps.get_model("supplies", "SaleSupply")
    for supply in Supply.objects.filter(category__is_filament=True):
        peso = _peso(supply)
        stock = SupplyStock.objects.filter(supply=supply).first()
        if stock:
            stock.quantity //= peso
            stock.uncosted = min(stock.uncosted // peso, stock.quantity)
            stock.save(update_fields=["quantity", "uncosted"])
        for movement in SupplyMovement.objects.filter(supply=supply):
            movement.delta = movement.delta // peso or (1 if movement.delta > 0 else -1)
            movement.balance_after //= peso
            movement.save(update_fields=["delta", "balance_after"])
        for line in SaleSupply.objects.filter(supply=supply):
            line.requested = max(1, line.requested // peso)
            line.taken = min(line.taken // peso, line.requested)
            line.zero_cost_qty = min(line.zero_cost_qty // peso, line.taken)
            line.save(update_fields=["requested", "taken", "zero_cost_qty"])
        supply.unit = "rolo"
        supply.save(update_fields=["unit"])


def criar_componentes(apps, schema_editor):
    SupplyCategory = apps.get_model("supplies", "SupplyCategory")
    nomes = {nome.casefold() for nome in SupplyCategory.objects.values_list("name", flat=True)}
    if "componentes" not in nomes:
        SupplyCategory.objects.create(name="Componentes", is_filament=False, counts_as_expense=False)


class Migration(migrations.Migration):
    dependencies = [
        ("supplies", "0008_componentes_e_producao"),
        ("sales", "0007_custo_dos_insumos_na_venda"),
    ]

    operations = [
        migrations.RunPython(para_gramas, para_rolos),
        migrations.RunPython(criar_componentes, migrations.RunPython.noop),
    ]
