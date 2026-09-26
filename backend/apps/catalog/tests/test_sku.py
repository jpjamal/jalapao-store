from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Product
from apps.inventory.models import Stock


class AutomaticSkuTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(get_user_model().objects.create_superuser("sku-admin", password="test-pass"))

    def test_new_products_get_unique_sequential_skus_and_separate_stock(self):
        first = self.client.post(
            "/api/v1/products/", {"name": "Luminária Pimentão", "kind": "resale"}, format="json"
        )
        second = self.client.post(
            "/api/v1/products/", {"name": "Luminária Pimentão", "kind": "resale"}, format="json"
        )
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        first_sku = first.json()["sku"]
        second_sku = second.json()["sku"]
        self.assertRegex(first_sku, r"^SKU-LP-\d{4,}$")
        self.assertRegex(second_sku, r"^SKU-LP-\d{4,}$")
        self.assertEqual(int(second_sku.rsplit("-", 1)[1]), int(first_sku.rsplit("-", 1)[1]) + 1)
        self.assertEqual(first.json()["quantity"], 0)
        product = Product.objects.get(pk=first.json()["id"])
        Stock.objects.filter(product=product).update(quantity=3)
        product.refresh_from_db()
        self.assertEqual(product.sku, first_sku)

    def test_api_cannot_override_or_change_sku(self):
        response = self.client.post(
            "/api/v1/products/", {"name": "Porta-escova", "sku": "MANUAL"}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        sku = response.json()["sku"]
        self.assertTrue(sku.startswith("SKU-PE-"))
        updated = self.client.patch(
            f"/api/v1/products/{response.json()['id']}/", {"sku": "ALTERADO", "name": "Outro nome"}, format="json"
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["sku"], sku)

    def test_existing_manual_sku_is_preserved(self):
        product = Product.objects.create(name="Legado", sku="LEGACY-123")
        self.assertEqual(product.sku, "LEGACY-123")
