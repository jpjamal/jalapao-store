"""Spec 031 — congela em cada compra se ela entra como despesa no Resultado do negócio.

As compras existentes recebem a regra atual da categoria do insumo. Depois da migração, mudar a
categoria ou a opção dela não reclassifica o histórico.
"""

from django.db import migrations, models


def copiar_regra_atual(apps, schema_editor):
    SupplyReceipt = apps.get_model("supplies", "SupplyReceipt")
    for receipt in SupplyReceipt.objects.select_related("supply__category").iterator():
        receipt.counts_as_expense_snapshot = receipt.supply.category.counts_as_expense
        receipt.save(update_fields=["counts_as_expense_snapshot"])


class Migration(migrations.Migration):
    dependencies = [("supplies", "0004_despesa_por_categoria")]

    operations = [
        migrations.AddField(
            model_name="supplyreceipt",
            name="counts_as_expense_snapshot",
            field=models.BooleanField(null=True),
        ),
        migrations.RunPython(copiar_regra_atual, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="supplyreceipt",
            name="counts_as_expense_snapshot",
            field=models.BooleanField(),
        ),
    ]
