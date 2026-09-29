"""Spec 022 — categorias no lugar do tipo, e marca, modelo e peso no produto.

Os produtos atuais mudam de tipo para categoria: impressão 3D vira "Produção Impressão 3D" e
revenda vira "Eletrônicos". Os nomes ficam escritos aqui de propósito: migração não depende do
código do app, que muda com o tempo.
"""

import uuid

import django.core.validators
import django.db.models.deletion
import django.db.models.functions.text
from django.db import migrations, models


def tipo_para_categoria(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    Product = apps.get_model("catalog", "Product")
    eletronicos = Category.objects.create(name="Eletrônicos")
    producao = Category.objects.create(name="Produção Impressão 3D", uses_printing_profile=True)
    Product.objects.filter(kind="printing").update(category=producao)
    Product.objects.exclude(kind="printing").update(category=eletronicos)


def categoria_para_tipo(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    Product.objects.filter(category__uses_printing_profile=True).update(kind="printing")
    Product.objects.filter(category__uses_printing_profile=False).update(kind="resale")


class Migration(migrations.Migration):
    dependencies = [("catalog", "0006_gtin")]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=100)),
                ("uses_printing_profile", models.BooleanField(default=False)),
                ("active", models.BooleanField(default=True)),
            ],
            options={"verbose_name_plural": "categories", "ordering": ["name", "id"]},
        ),
        migrations.AddConstraint(
            model_name="category",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("name"), name="category_name_unique_ci"
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="category",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="products",
                to="catalog.category",
            ),
        ),
        migrations.AddField(model_name="product", name="brand", field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name="product", name="model", field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(
            model_name="product",
            name="weight_g",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                max_digits=10,
                null=True,
                validators=[django.core.validators.MinValueValidator(0)],
            ),
        ),
        migrations.RunPython(tipo_para_categoria, categoria_para_tipo),
        migrations.AlterField(
            model_name="product",
            name="category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, related_name="products", to="catalog.category"
            ),
        ),
        migrations.RemoveField(model_name="product", name="kind"),
    ]
