from django.db import migrations


def seed_costs(apps, schema_editor):
    Item = apps.get_model("sales", "SaleItem")
    for item in Item.objects.using(schema_editor.connection.alias).iterator():
        item.cost_total = item.unit_cost * item.quantity
        item.save(using=schema_editor.connection.alias, update_fields=["cost_total"])


class Migration(migrations.Migration):
    dependencies = [("sales", "0002_saleitem_cost_total")]
    operations = [migrations.RunPython(seed_costs, migrations.RunPython.noop)]
