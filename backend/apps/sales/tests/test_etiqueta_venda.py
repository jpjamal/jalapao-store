import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Product
from apps.inventory.services import adjust_stock
from apps.sales.models import SaleLabel


ZPL = "^XA^FO20,20^FDPedido 2601010ABCDEFG^FS^FO20,60^FDDESTINATARIO^FS^XZ"


class SaleLabelApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("label-owner")
        self.product = Product.objects.create(name="Controle", cost_price=Decimal("10"))
        adjust_stock(
            product_id=self.product.id,
            delta=10,
            reason="Estoque inicial",
            actor=self.user,
            unit_cost=Decimal("10"),
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def body(self, **extra):
        return {
            "idempotency_key": str(uuid.uuid4()),
            "channel": "shopee",
            "items": [{"product_id": str(self.product.id), "quantity": 1, "unit_price": "25.00"}],
            **extra,
        }

    def test_create_saves_zpl_and_uses_order_as_blank_reference(self):
        response = self.client.post(
            "/api/v1/sales/",
            self.body(
                zpl=ZPL,
                label_filename="pedido.txt",
                label_order_id="2601010ABCDEFG",
                label_name="Maria da Silva",
                label_city="Palmas",
                label_state="TO",
            ),
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.content)
        sale = response.json()
        self.assertEqual(sale["reference"], "2601010ABCDEFG")
        self.assertTrue(sale["has_label"])
        self.assertEqual(sale["label_order_id"], "2601010ABCDEFG")
        self.assertNotIn("zpl", sale)
        saved = SaleLabel.objects.get(sale_id=sale["id"])
        self.assertEqual((saved.zpl, saved.source_name, saved.order_id), (ZPL, "pedido.txt", "2601010ABCDEFG"))
        self.assertEqual(
            (saved.recipient_name, saved.recipient_city, saved.recipient_state),
            ("Maria da Silva", "Palmas", "TO"),
        )

        label = self.client.get(f"/api/v1/sales/{sale['id']}/label/")
        self.assertEqual(label.status_code, 200)
        self.assertEqual(label.json()["zpl"], ZPL)

    def test_invalid_or_incomplete_zpl_is_rejected_without_creating_sale(self):
        response = self.client.post("/api/v1/sales/", self.body(zpl="texto qualquer"), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("zpl", response.json()["errors"])
        self.assertFalse(SaleLabel.objects.exists())

        detached = self.client.post(
            "/api/v1/sales/",
            self.body(label_order_id="2601010ABCDEFG"),
            format="json",
        )
        self.assertEqual(detached.status_code, 400)

    def test_label_can_be_added_later_and_does_not_replace_manual_reference(self):
        created = self.client.post(
            "/api/v1/sales/", self.body(reference="Balcão"), format="json"
        ).json()
        response = self.client.put(
            f"/api/v1/sales/{created['id']}/label/",
            {
                "zpl": ZPL,
                "source_name": "nova.txt",
                "order_id": "2601010ABCDEFG",
                "recipient_name": "Nome corrigido",
                "recipient_city": "Gurupi",
                "recipient_state": "TO",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        detail = self.client.get(f"/api/v1/sales/{created['id']}/").json()
        self.assertEqual(detail["reference"], "Balcão")
        self.assertTrue(detail["has_label"])
        saved = SaleLabel.objects.get(sale_id=created["id"])
        self.assertEqual((saved.recipient_name, saved.recipient_city), ("Nome corrigido", "Gurupi"))

        blank = self.client.post("/api/v1/sales/", self.body(), format="json").json()
        added = self.client.put(
            f"/api/v1/sales/{blank['id']}/label/",
            {"zpl": ZPL, "order_id": "2601010ABCDEFG"},
            format="json",
        )
        self.assertEqual(added.status_code, 200)
        self.assertEqual(self.client.get(f"/api/v1/sales/{blank['id']}/").json()["reference"], "2601010ABCDEFG")

    def test_label_write_requires_sale_change_permission(self):
        created = self.client.post("/api/v1/sales/", self.body(), format="json").json()
        reader = get_user_model().objects.create_user("label-reader")
        reader.user_permissions.add(Permission.objects.get(codename="view_sale"))
        client = APIClient()
        client.force_authenticate(reader)

        self.assertEqual(client.get(f"/api/v1/sales/{created['id']}/label/").status_code, 404)
        denied = client.put(
            f"/api/v1/sales/{created['id']}/label/",
            {"zpl": ZPL, "order_id": "2601010ABCDEFG"},
            format="json",
        )
        self.assertEqual(denied.status_code, 403)
