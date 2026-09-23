import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import connection, close_old_connections
from django.utils import timezone
from rest_framework.test import APIClient
from apps.catalog.models import Product
from apps.inventory.models import Stock, Receipt, Movement
from apps.inventory.services import create_receipt, pay_receipt, adjust_stock
from apps.sales.services import create_sale, receive_sale, cancel_sale
from apps.finance.models import CashEntry


class ReceiptTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("buyer")
        self.product = Product.objects.create(sku="COST", name="Produto", cost_price=99)
        Stock.objects.create(product=self.product)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def data(self, quantity=10, cost="10", kind="purchase"):
        return dict(
            idempotency_key=uuid.uuid4(),
            product_id=self.product.id,
            quantity=quantity,
            unit_cost=Decimal(cost),
            kind=kind,
            occurred_on=timezone.localdate(),
        )

    def buy(self, quantity=10, cost="10", kind="purchase"):
        return create_receipt(data=self.data(quantity, cost, kind), actor=self.user)

    def sell(self, quantity):
        return create_sale(
            data=dict(
                idempotency_key=uuid.uuid4(),
                channel="direct",
                items=[dict(product_id=self.product.id, quantity=quantity, unit_price=Decimal(25))],
            ),
            actor=self.user,
        )

    def test_weighted_average_reference_sale_and_cancellation(self):
        self.buy()
        self.buy(cost="14")
        stock = Stock.objects.get(product=self.product)
        self.assertEqual((stock.quantity, stock.value, stock.average_cost), (20, Decimal(240), Decimal(12)))
        self.product.cost_price = 500
        self.product.save()
        sale = self.sell(2)
        self.assertEqual((sale.cost_total, sale.profit), (Decimal(24), Decimal(26)))
        self.assertEqual(sale.items.get().cost_total, Decimal(24))
        receive_sale(sale_id=sale.id, actor=self.user)
        self.assertEqual(CashEntry.objects.get().amount, Decimal(50))
        self.buy(2, "30")
        cancel_sale(sale_id=sale.id, actor=self.user)
        cancel_sale(sale_id=sale.id, actor=self.user)
        stock.refresh_from_db()
        self.assertEqual((stock.quantity, stock.value), (22, Decimal(300)))
        report = self.client.get("/api/v1/dashboard/").json()
        self.assertEqual(Decimal(report["stock_value"]), 300)
        self.assertEqual(Decimal(report["cash_balance"]), 0)

    def test_rounding_conserves_cents_and_empty_stock(self):
        self.buy(1, "0.01")
        self.buy(2, "0.00")
        sales = [self.sell(1) for _ in range(3)]
        self.assertEqual(sum(s.cost_total for s in sales), Decimal("0.01"))
        stock = Stock.objects.get(product=self.product)
        self.assertEqual((stock.quantity, stock.value), (0, 0))
        for sale in sales:
            cancel_sale(sale_id=sale.id, actor=self.user)
        stock.refresh_from_db()
        self.assertEqual((stock.quantity, stock.value), (3, Decimal("0.01")))

    def test_receipt_and_payment_are_idempotent(self):
        data = self.data()
        receipt = create_receipt(data=data, actor=self.user)
        self.assertEqual(create_receipt(data=data, actor=self.user).id, receipt.id)
        self.assertEqual(Receipt.objects.count(), 1)
        self.assertEqual(Movement.objects.count(), 1)
        self.assertFalse(CashEntry.objects.exists())
        url = f"/api/v1/receipts/{receipt.id}/pay/"
        for _ in range(2):
            self.assertEqual(
                self.client.post(url, {"occurred_on": str(timezone.localdate())}).status_code, 200
            )
        self.assertEqual(CashEntry.objects.get().amount, 100)
        self.assertEqual(CashEntry.objects.get().receipt_id, receipt.id)
        data["unit_cost"] = "11"
        response = self.client.post("/api/v1/receipts/", data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Stock.objects.get(product=self.product).quantity, 10)

    def test_production_snapshot_and_no_automatic_payment(self):
        receipt = self.buy(3, "6.83", "production")
        self.assertEqual(receipt.total, Decimal("20.49"))
        self.assertFalse(CashEntry.objects.exists())
        response = self.client.post(
            f"/api/v1/receipts/{receipt.id}/pay/", {"occurred_on": str(timezone.localdate())}
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(CashEntry.objects.exists())

    def test_invalid_entries_roll_back_and_permissions_apply(self):
        for changes in (
            {"quantity": 0},
            {"unit_cost": "-1"},
            {"unit_cost": "999999999999.99"},
            {"product_id": uuid.uuid4()},
            {"occurred_on": str(timezone.localdate() + timedelta(days=1))},
        ):
            response = self.client.post("/api/v1/receipts/", self.data() | changes, format="json")
            self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(Receipt.objects.exists())
        self.assertFalse(Movement.objects.exists())
        user = get_user_model().objects.create_user("restricted")
        user.user_permissions.add(Permission.objects.get(codename="add_receipt"))
        self.client.force_authenticate(user)
        self.assertEqual(self.client.post("/api/v1/receipts/", self.data(), format="json").status_code, 403)
        self.assertEqual(self.client.get("/api/v1/receipts/").status_code, 403)

    def test_purchase_api_and_payment_permission(self):
        response = self.client.post("/api/v1/receipts/", self.data(), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        receipt_id = response.data["id"]
        self.assertEqual(
            self.client.patch(f"/api/v1/receipts/{receipt_id}/", {"quantity": 20}).status_code, 405
        )
        user = get_user_model().objects.create_user("stock-only")
        user.user_permissions.add(
            Permission.objects.get(codename="add_receipt"), Permission.objects.get(codename="change_receipt")
        )
        self.client.force_authenticate(user)
        self.assertEqual(
            self.client.post(
                f"/api/v1/receipts/{receipt_id}/pay/", {"occurred_on": str(timezone.localdate())}
            ).status_code,
            403,
        )
        self.assertFalse(CashEntry.objects.exists())

    def test_adjustments_require_entry_cost_and_use_average_on_exit(self):
        self.buy(10, "12")
        payload = {"product": str(self.product.id), "delta": 1, "reason": "Inventário"}
        self.assertEqual(self.client.post("/api/v1/movements/", payload).status_code, 400)
        self.assertEqual(
            self.client.post("/api/v1/movements/", payload | {"unit_cost": "12"}).status_code, 201
        )
        adjust_stock(product_id=self.product.id, delta=-2, reason="Perda", actor=self.user)
        stock = Stock.objects.get(product=self.product)
        self.assertEqual((stock.quantity, stock.value), (9, 108))


class ReceiptConcurrencyTests(TransactionTestCase):
    def test_concurrent_receipts_and_payments(self):
        if connection.vendor != "postgresql":
            self.skipTest("Exige PostgreSQL real; executado no CI.")
        user = get_user_model().objects.create_user("buyer")
        product = Product.objects.create(sku="CONCURRENT", name="Produto")
        Stock.objects.create(product=product)
        data = dict(
            idempotency_key=uuid.uuid4(),
            product_id=product.id,
            kind="purchase",
            quantity=10,
            unit_cost=Decimal(10),
            occurred_on=timezone.localdate(),
        )

        def submit(_):
            close_old_connections()
            try:
                return create_receipt(data=data, actor=user).id
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            ids = list(pool.map(submit, range(2)))
        self.assertEqual(ids[0], ids[1])
        self.assertEqual(Stock.objects.get(product=product).value, 100)

        def pay(_):
            close_old_connections()
            try:
                pay_receipt(receipt_id=ids[0], occurred_on=timezone.localdate(), actor=user)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(pay, range(2)))
        self.assertEqual(CashEntry.objects.count(), 1)

    def test_purchase_and_sale_serialize_inventory_value(self):
        if connection.vendor != "postgresql":
            self.skipTest("Exige PostgreSQL real; executado no CI.")
        user = get_user_model().objects.create_user("stock-operator")
        product = Product.objects.create(sku="MIXED", name="Produto")
        Stock.objects.create(product=product, quantity=10, value=100)

        def operate(purchase):
            close_old_connections()
            try:
                if purchase:
                    create_receipt(
                        data=dict(
                            idempotency_key=uuid.uuid4(),
                            product_id=product.id,
                            kind="purchase",
                            quantity=10,
                            unit_cost=Decimal(14),
                            occurred_on=timezone.localdate(),
                        ),
                        actor=user,
                    )
                    return Decimal(0)
                sale = create_sale(
                    data=dict(
                        idempotency_key=uuid.uuid4(),
                        channel="direct",
                        items=[dict(product_id=product.id, quantity=2, unit_price=Decimal(25))],
                    ),
                    actor=user,
                )
                return sale.cost_total
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            costs = list(pool.map(operate, [True, False]))
        stock = Stock.objects.get(product=product)
        self.assertEqual(stock.quantity, 18)
        self.assertEqual(stock.value + sum(costs), Decimal(240))


class CostMigrationTests(TransactionTestCase):
    def test_existing_stock_and_sale_snapshots_are_preserved(self):
        from django.db.migrations.executor import MigrationExecutor

        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        before = [("inventory", "0001_initial"), ("sales", "0001_initial"), ("finance", "0001_initial")]
        executor.migrate(before)
        try:
            old = executor.loader.project_state(before).apps
            user = old.get_model("accounts", "User").objects.create(username="historical")
            product = old.get_model("catalog", "Product").objects.create(
                sku="OLD", name="Antigo", cost_price=10
            )
            old.get_model("inventory", "Stock").objects.create(product=product, quantity=3)
            old.get_model("inventory", "Movement").objects.create(
                product=product, delta=3, balance_after=3, reason="Antiga", actor=user
            )
            sale = old.get_model("sales", "Sale").objects.create(
                channel="direct",
                idempotency_key=uuid.uuid4(),
                request_hash="historical",
                gross=20,
                cost_total=8,
                net=20,
                profit=12,
                actor=user,
            )
            old.get_model("sales", "SaleItem").objects.create(
                sale=sale, product=product, product_name="Antigo", quantity=2, unit_price=10, unit_cost=4
            )
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate(latest)
        from apps.sales.models import SaleItem

        self.assertEqual(Stock.objects.get(product_id=product.id).value, 30)
        self.assertIsNone(Movement.objects.get(product_id=product.id).value_delta)
        item = SaleItem.objects.get(sale_id=sale.id)
        self.assertEqual(item.cost_total, 8)
        self.assertEqual(item.sale.profit, 12)
