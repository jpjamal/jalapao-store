"""Spec 024 — categorias de insumo e insumos, com as categorias iniciais.

Os nomes ficam escritos aqui de propósito: migração não depende do código do app, que muda com o
tempo. O dono pode renomear, acrescentar e desativar depois.
"""

import uuid
from decimal import Decimal

import django.core.validators
import django.db.models.deletion
import django.db.models.functions.text
from django.db import migrations, models

INICIAIS = [
    ("Filamentos", True),
    ("Embalagens", False),
    ("Etiquetas e papelaria", False),
    ("Colas e fitas", False),
    ("Acabamento", False),
    ("Ferramentas", False),
    ("Outros", False),
]


def criar_categorias(apps, schema_editor):
    SupplyCategory = apps.get_model("supplies", "SupplyCategory")
    for nome, is_filament in INICIAIS:
        SupplyCategory.objects.create(name=nome, is_filament=is_filament)


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SupplyCategory",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=100)),
                ("is_filament", models.BooleanField(default=False)),
                ("active", models.BooleanField(default=True)),
            ],
            options={"verbose_name_plural": "supply categories", "ordering": ["name", "id"]},
        ),
        migrations.AddConstraint(
            model_name="supplycategory",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("name"), name="supply_category_name_unique_ci"
            ),
        ),
        migrations.CreateModel(
            name="Supply",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=120)),
                ("unit", models.CharField(default="unidade", max_length=30)),
                ("notes", models.CharField(blank=True, max_length=500)),
                ("active", models.BooleanField(default=True)),
                ("material", models.CharField(blank=True, max_length=40)),
                ("color", models.CharField(blank=True, max_length=40)),
                (
                    "roll_weight_g",
                    models.DecimalField(
                        blank=True,
                        decimal_places=3,
                        max_digits=10,
                        null=True,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.001"))],
                    ),
                ),
                (
                    "roll_price",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=14,
                        null=True,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="supplies",
                        to="supplies.supplycategory",
                    ),
                ),
            ],
            options={"verbose_name_plural": "supplies", "ordering": ["name", "id"]},
        ),
        migrations.AddConstraint(
            model_name="supply",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("name"),
                models.F("category"),
                name="supply_name_unique_ci_per_category",
            ),
        ),
        migrations.RunPython(criar_categorias, migrations.RunPython.noop),
    ]
