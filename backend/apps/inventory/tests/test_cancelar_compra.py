import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.catalog.models import Product
from apps.finance.models import CashEntry
from apps.inventory.models import Movement, Receipt, Stock
from apps.inventory.services import adjust_stock, cancel_receipt, create_receipt, pay_receipt
from apps.sales.services import create_sale


class CancelReceiptTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("canceller")
        self.product = Product.objects.create(sku="CANCEL", name="Controle")
        Stock.objects.create(product=self.product)

    def buy(self, quantity=1, cost="100", kind="purchase"):
        return create_receipt(
            data=dict(
                idempotency_key=uuid.uuid4(),
                product_id=self.product.id,
                quantity=quantity,
                unit_cost=Decimal(cost),
                kind=kind,
                occurred_on=timezone.localdate(),
            ),
            actor=self.user,
        )

    def stock(self):
        stock = Stock.objects.get(product=self.product)
        return stock.quantity, stock.value

    def test_cancel_restores_exact_quantity_and_value_even_with_older_stock_at_other_cost(self):
        self.buy(quantity=2, cost="10")
        wrong = self.buy(quantity=1, cost="100")
        self.assertEqual(self.stock(), (3, Decimal("120.00")))
        cancelled = cancel_receipt(receipt_id=wrong.id, actor=self.user)
        self.assertEqual(cancelled.status, "cancelled")
        self.assertIsNotNone(cancelled.cancelled_at)
        self.assertEqual(self.stock(), (2, Decimal("20.00")))
        self.assertEqual(Receipt.objects.count(), 2)
        last = Movement.objects.order_by("-created_at", "-id").first()
        self.assertEqual((last.delta, last.value_delta), (-1, Decimal("-100.00")))
        self.assertIn("Cancelamento de compra", last.reason)

    def test_cancel_unpaid_purchase_creates_no_cash_entry(self):
        receipt = self.buy()
        cancel_receipt(receipt_id=receipt.id, actor=self.user)
        self.assertEqual(CashEntry.objects.count(), 0)
        self.assertEqual(self.stock(), (0, Decimal("0.00")))

    def test_cancel_paid_purchase_refunds_the_cash_once(self):
        receipt = self.buy(quantity=2, cost="50")
        pay_receipt(receipt_id=receipt.id, occurred_on=timezone.localdate(), actor=self.user)
        cancel_receipt(receipt_id=receipt.id, actor=self.user)
        cancel_receipt(receipt_id=receipt.id, actor=self.user)  # repetir não duplica o estorno
        entries = {e.direction: e for e in CashEntry.objects.all()}
        self.assertEqual(entries["out"].amount, Decimal("100.00"))
        self.assertEqual(entries["in"].amount, Decimal("100.00"))
        self.assertEqual(entries["in"].refund_of_receipt_id, receipt.id)
        self.assertEqual(CashEntry.objects.count(), 2)
        self.assertEqual(Movement.objects.filter(product=self.product).count(), 2)

    def test_cancel_production_has_no_cash_effect(self):
        receipt = self.buy(kind="production")
        cancel_receipt(receipt_id=receipt.id, actor=self.user)
        self.assertEqual(CashEntry.objects.count(), 0)
        self.assertEqual(self.stock(), (0, Decimal("0.00")))

    def test_cannot_cancel_after_other_movements_and_nothing_changes(self):
        receipt = self.buy(quantity=5, cost="10")
        create_sale(
            data=dict(
                idempotency_key=uuid.uuid4(),
                channel="direct",
                items=[dict(product_id=self.product.id, quantity=1, unit_price=Decimal(25))],
            ),
            actor=self.user,
        )
        before = self.stock()
        with self.assertRaises(ValidationError) as caught:
            cancel_receipt(receipt_id=receipt.id, actor=self.user)
        self.assertIn("receipt", caught.exception.message_dict)
        receipt.refresh_from_db()
        self.assertEqual(receipt.status, "confirmed")
        self.assertEqual(self.stock(), before)

    def test_cannot_cancel_after_manual_adjustment_or_newer_purchase(self):
        first = self.buy(quantity=2, cost="10")
        adjust_stock(product_id=self.product.id, delta=-1, reason="Perda", actor=self.user)
        with self.assertRaises(ValidationError):
            cancel_receipt(receipt_id=first.id, actor=self.user)
        newer = self.buy(quantity=1, cost="30")
        with self.assertRaises(ValidationError):
            cancel_receipt(receipt_id=first.id, actor=self.user)
        cancel_receipt(receipt_id=newer.id, actor=self.user)  # a mais recente ainda pode
        self.assertEqual(self.stock(), (1, Decimal("10.00")))

    def test_cancelled_purchase_cannot_be_paid(self):
        receipt = self.buy()
        cancel_receipt(receipt_id=receipt.id, actor=self.user)
        with self.assertRaises(ValidationError) as caught:
            pay_receipt(receipt_id=receipt.id, occurred_on=timezone.localdate(), actor=self.user)
        self.assertIn("status", caught.exception.message_dict)
        self.assertEqual(CashEntry.objects.count(), 0)


class CancelReceiptApiTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("api-canceller")
        self.product = Product.objects.create(sku="CANCEL-API", name="Controle")
        Stock.objects.create(product=self.product)
        self.receipt = create_receipt(
            data=dict(
                idempotency_key=uuid.uuid4(),
                product_id=self.product.id,
                quantity=3,
                unit_cost=Decimal("20"),
                kind="purchase",
                occurred_on=timezone.localdate(),
            ),
            actor=self.admin,
        )

    def test_api_cancels_and_lists_the_receipt_as_cancelled(self):
        client = APIClient()
        client.force_authenticate(self.admin)
        response = client.post(f"/api/v1/receipts/{self.receipt.id}/cancel/", {}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "cancelled")
        listed = client.get("/api/v1/receipts/").json()["results"]
        self.assertEqual([r["status"] for r in listed], ["cancelled"])

    def test_api_refuses_with_message_when_product_moved_afterwards(self):
        adjust_stock(product_id=self.product.id, delta=-1, reason="Perda", actor=self.admin)
        client = APIClient()
        client.force_authenticate(self.admin)
        response = client.post(f"/api/v1/receipts/{self.receipt.id}/cancel/", {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("receipt", response.json()["errors"])

    def test_api_requires_permissions(self):
        limited = get_user_model().objects.create_user("no-perms", password="x")
        client = APIClient()
        client.force_authenticate(limited)
        response = client.post(f"/api/v1/receipts/{self.receipt.id}/cancel/", {}, format="json")
        self.assertEqual(response.status_code, 403)
        self.receipt.refresh_from_db()
        self.assertEqual(self.receipt.status, "confirmed")
