"""Spec 026 — categorias nos lançamentos do Caixa.

Cria as categorias do sistema (só dos lançamentos automáticos) e as iniciais do dono, liga cada lançamento
que já existe pela origem e leva os manuais para "A classificar", que não conta no resultado: o sistema não
adivinha a categoria, e assim nenhum valor entra no resultado por engano. Os nomes ficam escritos aqui de
propósito: migração não depende do código do app, que muda com o tempo.
"""

import uuid

import django.db.models.deletion
import django.db.models.functions.text
from django.db import migrations, models

SISTEMA = [
    ("sale_received", "Venda recebida", "in"),
    ("sale_refund", "Estorno de venda", "out"),
    ("purchase", "Compra de produtos", "out"),
    ("purchase_refund", "Estorno de compra de produtos", "in"),
    ("supply_purchase", "Compra de insumos", "out"),
    ("supply_refund", "Estorno de compra de insumos", "in"),
    ("unclassified", "A classificar", "both"),
]

# (nome, direção, conta no resultado). Energia começa sem contar: a energia estimada já está no custo da peça.
INICIAIS = [
    ("Energia", "out", False),
    ("Internet e telefone", "out", True),
    ("Impostos e taxas", "out", True),
    ("Frete e envio", "out", True),
    ("Divulgação", "out", True),
    ("Equipamentos e manutenção", "out", True),
    ("Outras despesas", "out", True),
    ("Outras receitas", "in", True),
    ("Empréstimo recebido", "in", False),
    ("Pagamento de empréstimo", "out", False),
    ("Aporte do dono", "in", False),
    ("Retirada do dono", "out", False),
]


def classificar(apps, schema_editor):
    CashCategory = apps.get_model("finance", "CashCategory")
    CashEntry = apps.get_model("finance", "CashEntry")
    chaves = {}
    for chave, nome, direcao in SISTEMA:
        chaves[chave] = CashCategory.objects.create(
            name=nome, direction=direcao, counts_in_result=False, system_key=chave
        )
    for nome, direcao, conta in INICIAIS:
        CashCategory.objects.create(name=nome, direction=direcao, counts_in_result=conta)
    entradas = CashEntry.objects.all()
    entradas.filter(sale__isnull=False, direction="in").update(category=chaves["sale_received"])
    entradas.filter(sale__isnull=False).exclude(direction="in").update(category=chaves["sale_refund"])
    entradas.filter(sale__isnull=True, receipt__isnull=False).update(category=chaves["purchase"])
    entradas.filter(sale__isnull=True, receipt__isnull=True, refund_of_receipt__isnull=False).update(
        category=chaves["purchase_refund"]
    )
    entradas.filter(
        sale__isnull=True, receipt__isnull=True, refund_of_receipt__isnull=True, supply_receipt__isnull=False
    ).update(category=chaves["supply_purchase"])
    entradas.filter(
        sale__isnull=True,
        receipt__isnull=True,
        refund_of_receipt__isnull=True,
        supply_receipt__isnull=True,
        refund_of_supply_receipt__isnull=False,
    ).update(category=chaves["supply_refund"])
    entradas.filter(category__isnull=True).update(category=chaves["unclassified"])


class Migration(migrations.Migration):
    dependencies = [("finance", "0004_estoque_compras_insumos")]

    operations = [
        migrations.CreateModel(
            name="CashCategory",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=100)),
                (
                    "direction",
                    models.CharField(
                        choices=[("in", "Entrada"), ("out", "Saída"), ("both", "Entrada ou saída")], max_length=4
                    ),
                ),
                ("counts_in_result", models.BooleanField(default=True)),
                ("active", models.BooleanField(default=True)),
                ("system_key", models.CharField(blank=True, max_length=30, null=True, unique=True)),
            ],
            options={"verbose_name_plural": "cash categories", "ordering": ["name", "id"]},
        ),
        migrations.AddConstraint(
            model_name="cashcategory",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("name"), name="cash_category_name_unique_ci"
            ),
        ),
        migrations.AddField(
            model_name="cashentry",
            name="category",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="entries",
                to="finance.cashcategory",
            ),
        ),
        migrations.RunPython(classificar, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="cashentry",
            name="category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, related_name="entries", to="finance.cashcategory"
            ),
        ),
    ]
