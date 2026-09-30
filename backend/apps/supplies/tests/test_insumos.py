from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from apps.supplies.domain.pricing import normalize_material, price_per_gram, price_per_kg
from apps.supplies.models import Supply, SupplyCategory


class SupplyPricingTests(SimpleTestCase):
    def test_price_per_gram_and_per_kg(self):
        self.assertEqual(price_per_gram(Decimal("100"), Decimal("1000")), Decimal("0.1"))
        self.assertEqual(price_per_kg(Decimal("100"), Decimal("1000")), Decimal("100"))
        self.assertEqual(price_per_gram(Decimal("89.90"), Decimal("1000")), Decimal("0.0899"))
        self.assertEqual(price_per_kg(Decimal("50"), Decimal("500")), Decimal("100"))

    def test_price_per_gram_is_not_rounded(self):
        # R$ 100 por 750 g não dá uma dízima exata em 2 casas nem em 6: a conta guarda a divisão
        gram = price_per_gram(Decimal("100"), Decimal("750"))
        self.assertGreater(len(str(gram)), 10)
        self.assertEqual(round(gram * Decimal("750"), 10), Decimal("100"))

    def test_material_uses_the_suggested_spelling(self):
        self.assertEqual(normalize_material("pla"), "PLA")
        self.assertEqual(normalize_material("  petg "), "PETG")
        self.assertEqual(normalize_material("Pla+"), "PLA+")
        self.assertEqual(normalize_material("  Nylon   CF "), "Nylon CF")


class SupplyApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(get_user_model().objects.create_superuser("sup-admin", password="test-pass"))
        # a migração já semeia as categorias; em banco zerado por outro teste elas são criadas aqui
        self.filamentos, _ = SupplyCategory.objects.get_or_create(name="Filamentos", defaults={"is_filament": True})
        self.embalagens, _ = SupplyCategory.objects.get_or_create(name="Embalagens")

    def filament(self, **extra):
        body = {
            "category": str(self.filamentos.pk),
            "name": "Filamento Voolt",
            "material": "pla",
            "color": "Preto",
            "roll_weight_g": "1000",
            "roll_price": "100.00",
            **extra,
        }
        return self.client.post("/api/v1/supplies/", body, format="json")

    def test_initial_categories_exist_with_filament_flag(self):
        names = {c["name"]: c for c in self.client.get("/api/v1/supply-categories/").json()["results"]}
        self.assertTrue(names["Filamentos"]["is_filament"])
        self.assertFalse(names["Embalagens"]["is_filament"])

    def test_create_category_unique_ignoring_case_and_accent(self):
        created = self.client.post("/api/v1/supply-categories/", {"name": "  Etiquetas   térmicas "}, format="json")
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["name"], "Etiquetas térmicas")
        self.assertFalse(created.json()["is_filament"])
        clash = self.client.post("/api/v1/supply-categories/", {"name": "ETIQUETAS TÉRMICAS"}, format="json")
        self.assertEqual(clash.status_code, 400)

    def test_is_filament_locks_after_first_supply_and_no_delete(self):
        self.assertEqual(self.filament().status_code, 201)
        locked = self.client.patch(
            f"/api/v1/supply-categories/{self.filamentos.pk}/", {"is_filament": False}, format="json"
        )
        self.assertEqual(locked.status_code, 400)
        self.assertEqual(self.client.delete(f"/api/v1/supply-categories/{self.filamentos.pk}/").status_code, 405)
        off = self.client.patch(f"/api/v1/supply-categories/{self.filamentos.pk}/", {"active": False}, format="json")
        self.assertEqual(off.status_code, 200)

    def test_filament_gets_prices_per_gram_and_per_kg_and_normalized_material(self):
        response = self.filament()
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["material"], "PLA")
        self.assertEqual(body["price_per_gram"], "0.100000")
        self.assertEqual(body["price_per_kg"], "100.00")
        self.assertTrue(body["category_is_filament"])

    def test_filament_requires_roll_data(self):
        response = self.client.post(
            "/api/v1/supplies/", {"category": str(self.filamentos.pk), "name": "Sem dados"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        for field in ("material", "color", "roll_weight_g", "roll_price"):
            self.assertIn(field, response.json()["errors"])

    def test_non_filament_supply_has_no_filament_fields_and_needs_only_a_name(self):
        ok = self.client.post(
            "/api/v1/supplies/",
            {"category": str(self.embalagens.pk), "name": "Caixa pequena", "unit": "pacote"},
            format="json",
        )
        self.assertEqual(ok.status_code, 201)
        self.assertIsNone(ok.json()["price_per_kg"])
        bad = self.client.post(
            "/api/v1/supplies/",
            {"category": str(self.embalagens.pk), "name": "Caixa grande", "material": "PLA"},
            format="json",
        )
        self.assertEqual(bad.status_code, 400)
        self.assertIn("material", bad.json()["errors"])

    def test_name_is_unique_inside_the_category_only(self):
        self.client.post("/api/v1/supplies/", {"category": str(self.embalagens.pk), "name": "Fita"}, format="json")
        again = self.client.post(
            "/api/v1/supplies/", {"category": str(self.embalagens.pk), "name": " FITA "}, format="json"
        )
        self.assertEqual(again.status_code, 400)
        other = SupplyCategory.objects.create(name="Colas e fitas teste")
        elsewhere = self.client.post("/api/v1/supplies/", {"category": str(other.pk), "name": "Fita"}, format="json")
        self.assertEqual(elsewhere.status_code, 201)

    def test_cannot_move_between_filament_and_other_categories(self):
        created = self.client.post(
            "/api/v1/supplies/", {"category": str(self.embalagens.pk), "name": "Caixa"}, format="json"
        ).json()
        moved = self.client.patch(
            f"/api/v1/supplies/{created['id']}/", {"category": str(self.filamentos.pk)}, format="json"
        )
        self.assertEqual(moved.status_code, 400)
        other = SupplyCategory.objects.create(name="Outra comum")
        ok = self.client.patch(f"/api/v1/supplies/{created['id']}/", {"category": str(other.pk)}, format="json")
        self.assertEqual(ok.status_code, 200)

    def test_inactive_category_refuses_new_supplies(self):
        SupplyCategory.objects.filter(pk=self.embalagens.pk).update(active=False)
        response = self.client.post(
            "/api/v1/supplies/", {"category": str(self.embalagens.pk), "name": "Novo"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_supply_is_not_deleted_only_deactivated_and_filters_work(self):
        created = self.filament(color="Laranja", name="PLA Laranja").json()
        self.filament(color="Azul", name="PETG Azul", material="petg")
        self.assertEqual(self.client.delete(f"/api/v1/supplies/{created['id']}/").status_code, 405)
        self.client.patch(f"/api/v1/supplies/{created['id']}/", {"active": False}, format="json")
        active = self.client.get("/api/v1/supplies/?active=true").json()["results"]
        self.assertEqual([s["name"] for s in active], ["PETG Azul"])
        by_material = self.client.get("/api/v1/supplies/?material=PETG").json()["results"]
        self.assertEqual(len(by_material), 1)
        by_color = self.client.get("/api/v1/supplies/?search=laranja").json()["results"]
        self.assertEqual([s["name"] for s in by_color], ["PLA Laranja"])

    def test_materials_endpoint_lists_suggestions(self):
        results = self.client.get("/api/v1/supplies/materials/").json()["results"]
        self.assertIn("PLA", results)
        self.assertIn("PETG", results)

    def test_supplies_require_permissions(self):
        limited = get_user_model().objects.create_user("sup-limited", password="x")
        client = APIClient()
        client.force_authenticate(limited)
        self.assertEqual(client.get("/api/v1/supplies/").status_code, 403)
        self.assertEqual(Supply.objects.count(), 0)
