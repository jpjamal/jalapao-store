from django.db import migrations
from decimal import Decimal, ROUND_HALF_UP


def seed_values(apps, schema_editor):
    Stock = apps.get_model("inventory", "Stock")
    for stock in Stock.objects.using(schema_editor.connection.alias).select_related("product").iterator():
        stock.value = (stock.product.cost_price * stock.quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        stock.save(using=schema_editor.connection.alias, update_fields=["value"])


class Migration(migrations.Migration):
    dependencies = [("inventory", "0002_receipt_movement_value_after_movement_value_delta_and_more")]
    operations = [migrations.RunPython(seed_values, migrations.RunPython.noop)]
