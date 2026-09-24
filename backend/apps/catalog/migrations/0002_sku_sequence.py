from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="SkuSequence",
            fields=[("id", models.BigAutoField(primary_key=True, serialize=False))],
        ),
        migrations.AlterField(
            model_name="product",
            name="sku",
            field=models.CharField(blank=True, max_length=80, unique=True),
        ),
    ]
