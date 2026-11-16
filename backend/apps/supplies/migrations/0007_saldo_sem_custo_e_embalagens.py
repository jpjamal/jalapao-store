"""Spec 040 — custo dos insumos na venda.

1. Todo o saldo que já existe vira **sem custo** para as vendas: ou a compra dele já entrou como despesa
   no Resultado do negócio, ou o custo não é conhecido. Assim nada conta duas vezes.
2. O custo unitário de cada insumo começa com o da última compra confirmada (só para mostrar; as próximas
   compras e ajustes de entrada com custo passam a valer nas vendas).
3. A categoria **Embalagens** deixa de contar como despesa na compra: daqui para frente o custo da
   embalagem entra em cada venda. Compras antigas mantêm a classificação congelada (spec 031).
"""

from django.db import migrations


def preparar(apps, schema_editor):
    SupplyStock = apps.get_model("supplies", "SupplyStock")
    Supply = apps.get_model("supplies", "Supply")
    SupplyReceipt = apps.get_model("supplies", "SupplyReceipt")
    SupplyCategory = apps.get_model("supplies", "SupplyCategory")

    for stock in SupplyStock.objects.all():
        stock.uncosted = stock.quantity
        stock.save(update_fields=["uncosted"])

    for supply in Supply.objects.all():
        last = (
            SupplyReceipt.objects.filter(supply=supply, status="confirmed")
            .order_by("-created_at", "-id")
            .first()
        )
        if last is not None:
            supply.unit_cost = last.unit_cost
            supply.save(update_fields=["unit_cost"])

    for category in SupplyCategory.objects.all():
        if category.name.strip().casefold() == "embalagens":
            category.counts_as_expense = False
            category.save(update_fields=["counts_as_expense"])


class Migration(migrations.Migration):
    dependencies = [("supplies", "0006_custo_dos_insumos_na_venda")]

    operations = [migrations.RunPython(preparar, migrations.RunPython.noop)]
