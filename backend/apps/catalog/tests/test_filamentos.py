from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from apps.catalog.domain.pricing import filament_cost, printing_cost
from apps.catalog.models import PrintingProfile, Product
from apps.supplies.models import Supply, SupplyCategory

# peça de 2 h, 200 W, R$ 1,56 o kWh, sem mão de obra nem custo fixo, margem de 100%
BASE = dict(power_w="200", hours=2, minutes=0, energy_price_kwh="1.56", labor_cost="0", fixed_cost="0", markup_percent="100")
ENERGY = Decimal("0.624")  # 200 W x 2 h x 1,56 / 1000


class FilamentCostTests(SimpleTestCase):
    """Os mesmos números são conferidos na ferramenta do frontend (`custo3d.ts`)."""

    def test_multicolor_cost_sums_each_line_without_rounding_the_gram_price(self):
        # 30 g a R$ 0,10 o grama + 12 g a R$ 0,0899 o grama = 3,00 + 1,0788
        self.assertEqual(
            filament_cost([("30", "100", "1000"), ("12", "89.90", "1000")]), Decimal("4.0788")
        )

    def test_with_lines_the_total_is_rounded_only_at_the_end(self):
        cost, price = printing_cost(
            filament_price_kg="999", weight_g="999", **BASE,
            filament_lines=[("30", "100", "1000"), ("12", "89.90", "1000")],
        )
        # 4,0788 + 0,624 = 4,7028 -> 4,70; com 100% de margem 9,4056 -> 9,41
        self.assertEqual((cost, price), (Decimal("4.70"), Decimal("9.41")))

    def test_single_line_equals_the_legacy_formula(self):
        legacy = printing_cost(filament_price_kg="100", weight_g="42", **BASE)
        lines = printing_cost(filament_price_kg="1", weight_g="1", **BASE, filament_lines=[("42", "100", "1000")])
        self.assertEqual(legacy, lines)

    def test_without_lines_the_formula_is_the_same_as_always(self):
        cost, price = printing_cost(filament_price_kg="115", weight_g="45", **BASE)
        # 115/1000 x 45 = 5,175 ; + 0,624 = 5,799 -> 5,80 ; margem 100% -> 11,598 -> 11,60
        self.assertEqual((cost, price), (Decimal("5.80"), Decimal("11.60")))


class MulticolorApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(get_user_model().objects.create_superuser("fil-admin", password="test-pass"))
        self.category, _ = SupplyCategory.objects.get_or_create(name="Filamentos", defaults={"is_filament": True})
        self.black = Supply.objects.create(
            category=self.category, name="PLA Preto", material="PLA", color="Preto",
            roll_weight_g=Decimal("1000"), roll_price=Decimal("100.00"),
        )
        self.orange = Supply.objects.create(
            category=self.category, name="PLA Laranja", material="PLA", color="Laranja",
            roll_weight_g=Decimal("1000"), roll_price=Decimal("89.90"),
        )

    def printing(self, *lines, **extra):
        return {**BASE, "filaments": list(lines), **extra}

    def line(self, supply, grams, **extra):
        return {"filament": str(supply.pk), "grams": str(grams), **extra}

    def create(self, *lines, name="Peça multicolor", **extra):
        return self.client.post(
            "/api/v1/products/", {"name": name, "printing": self.printing(*lines, **extra)}, format="json"
        )

    def test_create_multicolor_piece_computes_cost_weight_and_average_price(self):
        response = self.create(self.line(self.black, 30), self.line(self.orange, 12))
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual((body["cost_price"], body["sale_price"]), ("4.70", "9.41"))
        self.assertEqual(body["category_name"], "Produção Impressão 3D")
        printing = body["printing"]
        self.assertEqual(Decimal(printing["weight_g"]), Decimal("42"))
        # média ponderada de R$ 4,0788 em 42 g: 97,114... por kg
        self.assertEqual(printing["filament_price_kg"], "97.11")
        lines = {line["filament_name"]: line for line in printing["filaments"]}
        self.assertEqual(lines["PLA Preto"]["price_per_kg"], "100.00")
        self.assertEqual(lines["PLA Laranja"]["color"], "Laranja")
        self.assertFalse(lines["PLA Preto"]["price_outdated"])

    def test_changing_the_filament_price_does_not_change_existing_pieces(self):
        created = self.create(self.line(self.black, 42)).json()
        Supply.objects.filter(pk=self.black.pk).update(roll_price=Decimal("200.00"))
        fetched = self.client.get(f"/api/v1/products/{created['id']}/").json()
        self.assertEqual(fetched["cost_price"], created["cost_price"])
        self.assertTrue(fetched["printing"]["filaments"][0]["price_outdated"])
        # salvar de novo com a mesma linha mantém o preço antigo
        resaved = self.client.patch(
            f"/api/v1/products/{created['id']}/",
            {"printing": self.printing(self.line(self.black, 42))},
            format="json",
        ).json()
        self.assertEqual(resaved["cost_price"], created["cost_price"])
        self.assertTrue(resaved["printing"]["filaments"][0]["price_outdated"])

    def test_refresh_price_brings_the_current_price(self):
        created = self.create(self.line(self.black, 42)).json()
        Supply.objects.filter(pk=self.black.pk).update(roll_price=Decimal("200.00"))
        refreshed = self.client.patch(
            f"/api/v1/products/{created['id']}/",
            {"printing": self.printing(self.line(self.black, 42, refresh_price=True))},
            format="json",
        ).json()
        self.assertNotEqual(refreshed["cost_price"], created["cost_price"])
        self.assertFalse(refreshed["printing"]["filaments"][0]["price_outdated"])
        self.assertEqual(refreshed["printing"]["filaments"][0]["price_per_kg"], "200.00")

    def test_editing_grams_and_removing_a_line_recomputes(self):
        created = self.create(self.line(self.black, 30), self.line(self.orange, 12)).json()
        edited = self.client.patch(
            f"/api/v1/products/{created['id']}/", {"printing": self.printing(self.line(self.black, 50))}, format="json"
        ).json()
        self.assertEqual(len(edited["printing"]["filaments"]), 1)
        self.assertEqual(Decimal(edited["printing"]["weight_g"]), Decimal("50"))
        # 50 g x 0,10 = 5,00 + 0,624 = 5,624 -> 5,62
        self.assertEqual(edited["cost_price"], "5.62")

    def test_going_back_to_manual_keeps_the_weight_and_uses_the_typed_price(self):
        created = self.create(self.line(self.black, 40)).json()
        manual = self.client.patch(
            f"/api/v1/products/{created['id']}/",
            {"printing": {**BASE, "filaments": [], "filament_price_kg": "115"}},
            format="json",
        ).json()
        self.assertEqual(manual["printing"]["filaments"], [])
        self.assertEqual(Decimal(manual["printing"]["weight_g"]), Decimal("40"))
        # 115/1000 x 40 = 4,60 + 0,624 = 5,224 -> 5,22
        self.assertEqual(manual["cost_price"], "5.22")

    def test_piece_without_lines_still_works_as_before(self):
        response = self.client.post(
            "/api/v1/products/",
            {"name": "Peça comum", "printing": {**BASE, "filament_price_kg": "115", "weight_g": "45"}},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual((response.json()["cost_price"], response.json()["sale_price"]), ("5.80", "11.60"))

    def test_weight_or_lines_are_required(self):
        response = self.client.post(
            "/api/v1/products/", {"name": "Sem peso", "printing": {**BASE, "filament_price_kg": "115"}}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("printing", response.json()["errors"])

    def test_line_validations(self):
        repeated = self.create(self.line(self.black, 10), self.line(self.black, 5))
        self.assertEqual(repeated.status_code, 400)
        zero = self.create(self.line(self.black, 0))
        self.assertEqual(zero.status_code, 400)
        crowd = []
        for i in range(9):
            crowd.append(
                self.line(
                    Supply.objects.create(
                        category=self.category, name=f"Cor {i}", material="PLA", color=str(i),
                        roll_weight_g=Decimal("1000"), roll_price=Decimal("90.00"),
                    ),
                    5,
                )
            )
        self.assertEqual(self.create(*crowd).status_code, 400)
        self.assertEqual(self.create(*crowd[:8], name="Oito cores").status_code, 201)

    def test_only_active_filament_supplies_can_be_chosen(self):
        other, _ = SupplyCategory.objects.get_or_create(name="Embalagens")
        box = Supply.objects.create(category=other, name="Caixa")
        self.assertEqual(self.create(self.line(box, 10)).status_code, 400)
        Supply.objects.filter(pk=self.orange.pk).update(active=False)
        self.assertEqual(self.create(self.line(self.orange, 10)).status_code, 400)

    def test_inactive_filament_stays_on_pieces_that_already_use_it(self):
        created = self.create(self.line(self.black, 20), self.line(self.orange, 10)).json()
        Supply.objects.filter(pk=self.orange.pk).update(active=False)
        again = self.client.patch(
            f"/api/v1/products/{created['id']}/",
            {"printing": self.printing(self.line(self.black, 25), self.line(self.orange, 10))},
            format="json",
        )
        self.assertEqual(again.status_code, 200)

    def test_profile_weight_matches_the_sum_and_prices_method_reads_lines(self):
        created = self.create(self.line(self.black, 30), self.line(self.orange, 12)).json()
        profile = PrintingProfile.objects.get(product_id=created["id"])
        self.assertEqual(profile.prices(), (Decimal("4.70"), Decimal("9.41")))
        self.assertEqual(Product.objects.get(pk=created["id"]).cost_price, Decimal("4.70"))
