import json
import tempfile
import uuid
from decimal import Decimal
from pathlib import Path
from django.test import TestCase, TransactionTestCase
from django.db import connection, close_old_connections
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from apps.catalog.models import Product
from apps.catalog.domain import printing_cost
from apps.inventory.models import Stock, Movement
from apps.inventory.services import adjust_stock
from apps.sales.models import Sale
from apps.sales.services import create_sale, receive_sale, cancel_sale
from apps.finance.models import CashEntry
from apps.integrations.models import OutboxEvent


class StoreTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("operator", password="test-password-123")
        self.product = Product.objects.create(
            sku="TEST", name="Peça", cost_price=Decimal("10"), sale_price=Decimal("25")
        )
        Stock.objects.create(product=self.product)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def data(self, quantity=2):
        return {
            "idempotency_key": uuid.uuid4(),
            "channel": "direct",
            "platform_fee": Decimal("3"),
            "discount": Decimal("2"),
            "shipping_cost": Decimal("5"),
            "items": [{"product_id": self.product.id, "quantity": quantity, "unit_price": Decimal("25")}],
        }

    def stock(self, quantity=5):
        adjust_stock(product_id=self.product.id, delta=quantity, reason="Entrada", actor=self.user)

    def test_3d_formula_and_decimal_time(self):
        cost, price = printing_cost(
            filament_price_kg="115",
            weight_g="45",
            power_w="200",
            hours=5,
            minutes=18,
            energy_price_kwh="1.56",
            labor_cost="0",
            fixed_cost="0",
            markup_percent="100",
        )
        self.assertEqual((cost, price), (Decimal("6.83"), Decimal("13.66")))

    def test_anonymous_and_model_permissions(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/v1/products/").status_code, 401)
        user = get_user_model().objects.create_user("reader", password="test-password-123")
        self.client.force_authenticate(user)
        self.assertEqual(self.client.get("/api/v1/products/").status_code, 403)
        user.user_permissions.add(Permission.objects.get(codename="view_product"))
        self.client.force_authenticate(get_user_model().objects.get(pk=user.pk))
        self.assertEqual(self.client.get("/api/v1/products/").status_code, 200)
        self.assertEqual(self.client.post("/api/v1/products/", {"name": "x", "sku": "x"}).status_code, 403)

    def test_jwt_login_refresh_blacklist(self):
        self.client.force_authenticate(None)
        pair = self.client.post(
            "/api/v1/auth/token/", {"username": "operator", "password": "test-password-123"}
        ).json()
        self.assertIn("access", pair)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + pair["access"])
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 200)
        refreshed = self.client.post("/api/v1/auth/refresh/", {"refresh": pair["refresh"]})
        self.assertEqual(refreshed.status_code, 200)
        self.assertEqual(
            self.client.post("/api/v1/auth/refresh/", {"refresh": pair["refresh"]}).status_code, 401
        )
        self.assertEqual(
            self.client.post("/api/v1/auth/logout/", {"refresh": refreshed.json()["refresh"]}).status_code,
            200,
        )
        self.assertEqual(
            self.client.post("/api/v1/auth/refresh/", {"refresh": refreshed.json()["refresh"]}).status_code,
            401,
        )

    def test_sale_inventory_profit_snapshot_and_idempotency(self):
        self.stock()
        data = self.data()
        sale = create_sale(data=data, actor=self.user)
        self.assertEqual(sale.net, Decimal("40"))
        self.assertEqual(sale.profit, Decimal("20"))
        self.assertEqual(Stock.objects.get(product=self.product).quantity, 3)
        self.assertEqual(create_sale(data=data, actor=self.user).id, sale.id)
        self.assertEqual(Sale.objects.count(), 1)
        self.product.cost_price = Decimal("99")
        self.product.save()
        sale.refresh_from_db()
        self.assertEqual(sale.items.first().unit_cost, Decimal("10"))
        self.assertEqual(sale.profit, Decimal("20"))
        data["discount"] = Decimal("1")
        with self.assertRaises(ValidationError):
            create_sale(data=data, actor=self.user)

    def test_insufficient_stock_rolls_back_every_effect(self):
        self.stock(1)
        with self.assertRaises(ValidationError):
            create_sale(data=self.data(), actor=self.user)
        self.assertEqual(Sale.objects.count(), 0)
        self.assertEqual(Movement.objects.count(), 1)
        self.assertEqual(OutboxEvent.objects.count(), 1)
        self.assertEqual(Stock.objects.get(product=self.product).quantity, 1)

    def test_multiline_failure_rolls_back_first_line(self):
        self.stock()
        other = Product.objects.create(sku="EMPTY", name="Sem estoque")
        Stock.objects.create(product=other)
        data = self.data()
        data["items"].append({"product_id": other.id, "quantity": 1, "unit_price": Decimal("10")})
        with self.assertRaises(ValidationError):
            create_sale(data=data, actor=self.user)
        self.assertEqual(Stock.objects.get(product=self.product).quantity, 5)
        self.assertFalse(Sale.objects.exists())

    def test_receipt_cancellation_and_cash_idempotency(self):
        self.stock()
        sale = create_sale(data=self.data(), actor=self.user)
        self.assertFalse(CashEntry.objects.exists())
        receive_sale(sale_id=sale.id, actor=self.user)
        receive_sale(sale_id=sale.id, actor=self.user)
        self.assertEqual(CashEntry.objects.count(), 1)
        cancel_sale(sale_id=sale.id, actor=self.user)
        cancel_sale(sale_id=sale.id, actor=self.user)
        self.assertEqual(Stock.objects.get(product=self.product).quantity, 5)
        self.assertEqual(CashEntry.objects.count(), 2)
        with self.assertRaises(ValidationError):
            receive_sale(sale_id=sale.id, actor=self.user)
        report = self.client.get("/api/v1/dashboard/").json()
        self.assertEqual(Decimal(report["cash_balance"]), 0)
        self.assertEqual(Decimal(report["gross"]), 0)

    def test_api_validates_prices_quantities_and_cash(self):
        bad = self.client.post(
            "/api/v1/products/", {"sku": "NEG", "name": "Negativo", "cost_price": "-1"}, format="json"
        )
        self.assertEqual(bad.status_code, 400)
        self.assertIn("errors", bad.json())
        self.assertEqual(
            self.client.post(
                "/api/v1/movements/",
                {"product": str(self.product.id), "delta": 0, "reason": "Zero"},
                format="json",
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/api/v1/cash/",
                {"direction": "in", "amount": "0", "description": "zero", "occurred_on": "2026-09-23"},
                format="json",
            ).status_code,
            400,
        )

    def test_api_sale_receive_cancel(self):
        self.stock()
        data = json.loads(json.dumps(self.data(), default=str))
        response = self.client.post("/api/v1/sales/", data, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        sale_id = response.json()["id"]
        self.assertEqual(self.client.post(f"/api/v1/sales/{sale_id}/receive/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/sales/{sale_id}/cancel/").status_code, 200)

    def test_import_is_idempotent_and_does_not_overwrite(self):
        payload = {
            "versao": 1,
            "itens": [
                {
                    "id": "legacy1",
                    "nome": "Antigo",
                    "tipo": "impressao3d",
                    "entradas": {
                        "precoKg": 115,
                        "gramas": 45,
                        "consumo": 200,
                        "horas": 5,
                        "minutos": 18,
                        "kwh": "1.56",
                        "margem": 100,
                    },
                }
            ],
        }
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "products.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            call_command("import_legacy", str(path), verbosity=0)
            product = Product.objects.get(legacy_id="legacy1")
            self.assertEqual(product.cost_price, Decimal("6.83"))
            product.name = "Nome novo"
            product.save()
            call_command("import_legacy", str(path), verbosity=0)
            product.refresh_from_db()
            self.assertEqual(product.name, "Nome novo")
            self.assertEqual(product.stock.quantity, 0)


class ConcurrencyTests(TransactionTestCase):
    def test_postgres_prevents_overselling(self):
        if connection.vendor != "postgresql":
            self.skipTest("Concorrência exige PostgreSQL real; executada no CI.")
        from concurrent.futures import ThreadPoolExecutor

        users = [get_user_model().objects.create_user(f"operator{i}") for i in range(2)]
        product = Product.objects.create(sku="LAST", name="Última unidade", cost_price=1)
        Stock.objects.create(product=product, quantity=1)

        def buy(user):
            close_old_connections()
            try:
                create_sale(
                    data={
                        "idempotency_key": uuid.uuid4(),
                        "channel": "direct",
                        "items": [{"product_id": product.id, "quantity": 1, "unit_price": Decimal("10")}],
                    },
                    actor=user,
                )
                return True
            except ValidationError:
                return False
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(buy, users))
        self.assertEqual(sorted(results), [False, True])
        self.assertEqual(Stock.objects.get(product=product).quantity, 0)
        self.assertEqual(Sale.objects.count(), 1)
