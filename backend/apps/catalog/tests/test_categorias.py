from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from apps.catalog.models import Category, PrintingProfile, Product, default_category, printing_category

PRINTING = {
    "filament_price_kg": "115",
    "weight_g": "45",
    "power_w": "200",
    "hours": 2,
    "minutes": 0,
    "energy_price_kwh": "1.56",
    "labor_cost": "0",
    "fixed_cost": "0",
    "markup_percent": "100",
}


class CategoryApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(get_user_model().objects.create_superuser("cat-admin", password="test-pass"))
        # a migração 0007 já semeia as duas; em banco zerado por outro teste, elas são criadas aqui
        self.eletronicos, _ = Category.objects.get_or_create(name="Eletrônicos")
        self.producao, _ = Category.objects.get_or_create(
            name="Produção Impressão 3D", defaults={"uses_printing_profile": True}
        )

    def product(self, **extra):
        return self.client.post("/api/v1/products/", {"name": "Controle 8BitDo", **extra}, format="json")

    def test_create_and_list_categories_with_product_count(self):
        created = self.client.post("/api/v1/categories/", {"name": "  Jogos   e  acessórios "}, format="json")
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["name"], "Jogos e acessórios")
        self.assertFalse(created.json()["uses_printing_profile"])
        self.product(category=str(self.eletronicos.pk))
        rows = {c["name"]: c for c in self.client.get("/api/v1/categories/").json()["results"]}
        self.assertEqual(rows["Eletrônicos"]["products_count"], 1)
        self.assertEqual(rows["Produção Impressão 3D"]["products_count"], 0)

    def test_category_name_is_unique_ignoring_case(self):
        self.assertEqual(self.client.post("/api/v1/categories/", {"name": "eletrônicos"}, format="json").status_code, 400)
        other = self.client.post("/api/v1/categories/", {"name": "Games"}, format="json").json()
        clash = self.client.patch(f"/api/v1/categories/{other['id']}/", {"name": "ELETRÔNICOS"}, format="json")
        self.assertEqual(clash.status_code, 400)
        same = self.client.patch(f"/api/v1/categories/{other['id']}/", {"name": "GAMES"}, format="json")
        self.assertEqual(same.status_code, 200)

    def test_printing_flag_is_locked_once_the_category_has_products(self):
        self.product(category=str(self.eletronicos.pk))
        locked = self.client.patch(
            f"/api/v1/categories/{self.eletronicos.pk}/", {"uses_printing_profile": True}, format="json"
        )
        self.assertEqual(locked.status_code, 400)
        self.assertIn("uses_printing_profile", locked.json()["errors"])
        empty = self.client.post("/api/v1/categories/", {"name": "Vazia"}, format="json").json()
        free = self.client.patch(f"/api/v1/categories/{empty['id']}/", {"uses_printing_profile": True}, format="json")
        self.assertEqual(free.status_code, 200)

    def test_category_cannot_be_deleted_only_deactivated(self):
        self.assertEqual(self.client.delete(f"/api/v1/categories/{self.eletronicos.pk}/").status_code, 405)
        off = self.client.patch(f"/api/v1/categories/{self.eletronicos.pk}/", {"active": False}, format="json")
        self.assertEqual(off.status_code, 200)
        only_active = self.client.get("/api/v1/categories/?active=true").json()["results"]
        self.assertEqual([c["name"] for c in only_active], ["Produção Impressão 3D"])

    def test_product_without_category_gets_the_default_one(self):
        response = self.product()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["category"], str(self.eletronicos.pk))
        self.assertEqual(response.json()["category_name"], "Eletrônicos")

    def test_printing_parameters_without_category_go_to_the_printing_category(self):
        response = self.product(printing=PRINTING)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["category"], str(self.producao.pk))
        self.assertTrue(PrintingProfile.objects.filter(product_id=response.json()["id"]).exists())

    def test_printing_category_requires_parameters_and_others_refuse_them(self):
        missing = self.product(category=str(self.producao.pk))
        self.assertEqual(missing.status_code, 400)
        self.assertIn("printing", missing.json()["errors"])
        refused = self.product(category=str(self.eletronicos.pk), printing=PRINTING)
        self.assertEqual(refused.status_code, 400)
        self.assertIn("printing", refused.json()["errors"])

    def test_moving_a_product_out_of_printing_removes_its_profile(self):
        created = self.product(printing=PRINTING).json()
        moved = self.client.patch(
            f"/api/v1/products/{created['id']}/",
            {"category": str(self.eletronicos.pk), "cost_price": "10", "sale_price": "20"},
            format="json",
        )
        self.assertEqual(moved.status_code, 200)
        self.assertFalse(PrintingProfile.objects.filter(product_id=created["id"]).exists())
        back = self.client.patch(
            f"/api/v1/products/{created['id']}/", {"category": str(self.producao.pk)}, format="json"
        )
        self.assertEqual(back.status_code, 400)

    def test_inactive_category_cannot_receive_products_but_old_ones_keep_it(self):
        created = self.product(category=str(self.eletronicos.pk)).json()
        Category.objects.filter(pk=self.eletronicos.pk).update(active=False)
        self.assertEqual(self.product(category=str(self.eletronicos.pk)).status_code, 400)
        edited = self.client.patch(f"/api/v1/products/{created['id']}/", {"name": "Outro nome"}, format="json")
        self.assertEqual(edited.status_code, 200)
        same = self.client.patch(
            f"/api/v1/products/{created['id']}/", {"category": str(self.eletronicos.pk)}, format="json"
        )
        self.assertEqual(same.status_code, 200)

    def test_brand_model_and_weight_are_optional_and_searchable(self):
        bare = self.product(name="Sem marca")
        self.assertEqual(bare.json()["brand"], "")
        self.assertIsNone(bare.json()["weight_g"])
        full = self.product(name="Gamepad", brand="8BitDo", model="Pro 2", weight_g="275.500")
        self.assertEqual(full.status_code, 201)
        self.assertEqual(full.json()["model"], "Pro 2")
        self.assertEqual(full.json()["weight_g"], "275.500")
        found = self.client.get("/api/v1/products/?search=pro 2").json()["results"]
        self.assertEqual([p["id"] for p in found], [full.json()["id"]])
        by_brand = self.client.get("/api/v1/products/?search=8bitdo").json()["results"]
        self.assertEqual(len(by_brand), 1)

    def test_negative_weight_is_rejected(self):
        response = self.product(weight_g="-1")
        self.assertEqual(response.status_code, 400)
        self.assertIn("weight_g", response.json()["errors"])

    def test_products_filter_by_category(self):
        self.product(category=str(self.eletronicos.pk))
        self.product(printing=PRINTING)
        found = self.client.get(f"/api/v1/products/?category={self.producao.pk}").json()["results"]
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["category_name"], "Produção Impressão 3D")


class CategoryDefaultsTests(TestCase):
    def test_defaults_are_created_when_missing_and_survive_rename(self):
        self.assertEqual(default_category().name, "Eletrônicos")
        self.assertEqual(printing_category().name, "Produção Impressão 3D")
        Category.objects.filter(name="Eletrônicos").update(name="Games")
        self.assertEqual(default_category().name, "Games")
        self.assertEqual(Category.objects.count(), 2)

    def test_product_created_in_code_gets_the_default_category(self):
        product = Product.objects.create(name="Sem categoria")
        self.assertEqual(product.category.name, "Eletrônicos")


class KindToCategoryMigrationTests(TransactionTestCase):
    def test_existing_products_move_from_kind_to_category(self):
        from django.db.migrations.executor import MigrationExecutor

        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        before = [("catalog", "0006_gtin")]
        executor.migrate(before)
        try:
            old = executor.loader.project_state(before).apps
            Old = old.get_model("catalog", "Product")
            resale = Old.objects.create(sku="A-REV", name="Revenda", kind="resale")
            printed = Old.objects.create(sku="A-3D", name="Impressa", kind="printing")
        finally:
            MigrationExecutor(connection).migrate(latest)
        resale = Product.objects.get(pk=resale.pk)
        printed = Product.objects.get(pk=printed.pk)
        self.assertEqual(resale.category.name, "Eletrônicos")
        self.assertFalse(resale.category.uses_printing_profile)
        self.assertEqual(printed.category.name, "Produção Impressão 3D")
        self.assertTrue(printed.category.uses_printing_profile)
        self.assertEqual(resale.brand, "")
        self.assertIsNone(resale.weight_g)
