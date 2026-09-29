from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from apps.catalog.domain.gtin import check_digit, gtin_error, normalize_gtin
from apps.catalog.models import Product


class GtinDomainTests(SimpleTestCase):
    def test_known_valid_codes(self):
        for code in ["7891000100103", "4006381333931", "96385074", "036000291452", "10012345678902"]:
            self.assertIsNone(gtin_error(code), code)

    def test_check_digit(self):
        self.assertEqual(check_digit("400638133393"), 1)

    def test_rejects_bad_codes(self):
        self.assertIn("apenas números", gtin_error("78910001A0103"))
        self.assertIn("8, 12, 13 ou 14", gtin_error("12345"))
        self.assertIn("verificador", gtin_error("7891000100104"))

    def test_normalize_strips_spaces_and_hyphens(self):
        self.assertEqual(normalize_gtin(" 789-1000 100103 "), "7891000100103")


class GtinApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(get_user_model().objects.create_superuser("gtin-admin", password="test-pass"))

    def create(self, name, **extra):
        return self.client.post("/api/v1/products/", {"name": name, **extra}, format="json")

    def test_gtin_is_optional_and_many_products_can_have_none(self):
        first, second = self.create("Sem código A"), self.create("Sem código B", gtin="")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertIsNone(first.json()["gtin"])
        self.assertIsNone(second.json()["gtin"])

    def test_valid_gtin_is_saved_clean(self):
        response = self.create("Controle 8BitDo Preto", gtin=" 789 1000-100103 ")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["gtin"], "7891000100103")

    def test_invalid_gtin_is_rejected(self):
        response = self.create("Controle", gtin="7891000100104")
        self.assertEqual(response.status_code, 400)
        self.assertIn("gtin", response.json()["errors"])

    def test_duplicate_gtin_is_rejected_but_own_code_can_be_resent(self):
        first = self.create("Controle Preto", gtin="7891000100103")
        self.assertEqual(self.create("Controle Branco", gtin="7891000100103").status_code, 400)
        same = self.client.patch(
            f"/api/v1/products/{first.json()['id']}/", {"gtin": "7891000100103", "name": "Controle Preto 2"},
            format="json",
        )
        self.assertEqual(same.status_code, 200)

    def test_gtin_can_be_cleared(self):
        created = self.create("Controle", gtin="7891000100103")
        cleared = self.client.patch(f"/api/v1/products/{created.json()['id']}/", {"gtin": ""}, format="json")
        self.assertEqual(cleared.status_code, 200)
        self.assertIsNone(cleared.json()["gtin"])
        self.assertIsNone(Product.objects.get(pk=created.json()["id"]).gtin)

    def test_search_finds_product_by_gtin(self):
        self.create("Controle 8BitDo", gtin="7891000100103")
        self.create("Outro produto")
        found = self.client.get("/api/v1/products/?search=7891000100103").json()
        self.assertEqual([p["name"] for p in found["results"]], ["Controle 8BitDo"])
