import json
from decimal import Decimal
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.catalog.models import Product, PrintingProfile
from apps.inventory.models import Stock

FIELDS = {
    "precoKg": "filament_price_kg",
    "gramas": "weight_g",
    "consumo": "power_w",
    "horas": "hours",
    "minutos": "minutes",
    "kwh": "energy_price_kwh",
    "maoDeObra": "labor_cost",
    "custoFixo": "fixed_cost",
    "margem": "markup_percent",
}


class Command(BaseCommand):
    help = "Importa JSON legado atomicamente, sem sobrescrever IDs já migrados ou estimar estoque."

    def add_arguments(self, parser):
        parser.add_argument("path")

    @transaction.atomic
    def handle(self, *args, **options):
        data = json.loads(Path(options["path"]).read_text(encoding="utf-8-sig"))
        if data.get("versao") != 1 or not isinstance(data.get("itens"), list):
            raise CommandError("Envelope legado inválido; nada foi importado.")
        created = 0
        for item in data["itens"]:
            if not item.get("id") or not item.get("nome"):
                raise CommandError("Produto sem ID ou nome; importação revertida.")
            if Product.objects.filter(legacy_id=item["id"]).exists():
                continue
            if item.get("tipo") != "impressao3d":
                raise CommandError(f"Tipo legado não reconhecido: {item.get('tipo')}.")
            product = Product(legacy_id=item["id"], sku=item["id"], name=item["nome"], kind="printing")
            product.full_clean()
            product.save()
            values = {
                target: Decimal(str(item.get("entradas", {}).get(source, 0) or 0).replace(",", "."))
                for source, target in FIELDS.items()
            }
            profile = PrintingProfile(product=product, **values)
            profile.full_clean()
            profile.save()
            product.cost_price, product.sale_price = profile.prices()
            product.save()
            Stock.objects.create(product=product)
            created += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"{created} produtos importados; {len(data['itens']) - created} preservados. Estoques novos iniciam em zero."
            )
        )
