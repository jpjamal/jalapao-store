"""Spec 026 — opção "conta como despesa quando comprado" em cada categoria de insumo.

Nasce ligada (compra de insumo conta como despesa no Resultado do negócio) e é desligada nas categorias
cujo custo já está no custo da peça 3D: filamento (linhas de filamento) e acabamento e colas e fitas
(custos fixos). Os nomes ficam escritos aqui de propósito: migração não depende do código do app.
"""

from django.db import migrations, models

SEM_DESPESA = ["Filamentos", "Acabamento", "Colas e fitas"]


def desligar_onde_ja_esta_no_custo(apps, schema_editor):
    SupplyCategory = apps.get_model("supplies", "SupplyCategory")
    SupplyCategory.objects.filter(name__in=SEM_DESPESA).update(counts_as_expense=False)


class Migration(migrations.Migration):
    dependencies = [("supplies", "0003_insumos_na_venda")]

    operations = [
        migrations.AddField(
            model_name="supplycategory",
            name="counts_as_expense",
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(desligar_onde_ja_esta_no_custo, migrations.RunPython.noop),
    ]
