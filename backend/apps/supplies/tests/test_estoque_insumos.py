import uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connection
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.finance.models import CashEntry
from apps.supplies.models import Supply, SupplyCategory, SupplyMovement, SupplyReceipt, SupplyStock
from apps.supplies.services import (
    adjust_supply_stock,
    cancel_supply_receipt,
    create_supply_receipt,
    pay_supply_receipt,
)


class SupplyStockTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("supplier-admin")
        self.box_cat, _ = SupplyCategory.objects.get_or_create(name="Embalagens")
        self.fil_cat, _ = SupplyCategory.objects.get_or_create(name="Filamentos", defaults={"is_filament": True})
        self.box = Supply.objects.create(category=self.box_cat, name="Caixa pequena", unit="pacote")
        self.filament = Supply.objects.create(
            category=self.fil_cat, name="PLA Preto", material="PLA", color="Preto",
            roll_weight_g=Decimal("1000"), roll_price=Decimal("100.00"),
        )

    def buy(self, supply=None, quantity=2, cost="10.00", **extra):
        return create_supply_receipt(
            data=dict(
                idempotency_key=uuid.uuid4(),
                supply_id=(supply or self.box).id,
                quantity=quantity,
                unit_cost=Decimal(cost),
                occurred_on=timezone.localdate(),
                **extra,
            ),
            actor=self.user,
        )

    def balance(self, supply=None):
        stock = SupplyStock.objects.filter(supply=supply or self.box).first()
        return stock.quantity if stock else 0

    # ---- saldo, baixa e ajuste ----
    def test_adjust_records_a_movement_and_never_goes_negative(self):
        adjust_supply_stock(supply_id=self.box.id, delta=5, reason="Contagem inicial", actor=self.user)
        movement = adjust_supply_stock(supply_id=self.box.id, delta=-2, reason="Usei 2", actor=self.user)
        self.assertEqual((movement.delta, movement.balance_after, self.balance()), (-2, 3, 3))
        with self.assertRaises(ValidationError) as caught:
            adjust_supply_stock(supply_id=self.box.id, delta=-4, reason="Demais", actor=self.user)
        self.assertIn("quantity", caught.exception.message_dict)
        self.assertEqual(self.balance(), 3)

    def test_adjust_needs_a_reason_and_a_nonzero_quantity(self):
        for delta, reason in [(1, ""), (1, "   "), (0, "Nada")]:
            with self.assertRaises(ValidationError):
                adjust_supply_stock(supply_id=self.box.id, delta=delta, reason=reason, actor=self.user)
        self.assertEqual(SupplyMovement.objects.count(), 0)

    def test_inactive_supply_gives_baixa_but_takes_no_entries(self):
        adjust_supply_stock(supply_id=self.box.id, delta=3, reason="Inicial", actor=self.user)
        Supply.objects.filter(pk=self.box.pk).update(active=False)
        adjust_supply_stock(supply_id=self.box.id, delta=-1, reason="Sobra", actor=self.user)
        with self.assertRaises(ValidationError):
            adjust_supply_stock(supply_id=self.box.id, delta=1, reason="Entrada", actor=self.user)
        with self.assertRaises(ValidationError):
            self.buy()

    # ---- compra ----
    def test_purchase_enters_the_balance_and_is_unpaid(self):
        receipt = self.buy(quantity=3, cost="12.50", supplier="Loja X", reference="NF 1")
        self.assertEqual((receipt.total, receipt.status, receipt.paid_at), (Decimal("37.50"), "confirmed", None))
        self.assertEqual(self.balance(), 3)
        self.assertEqual(CashEntry.objects.count(), 0)
        movement = SupplyMovement.objects.get(receipt=receipt)
        self.assertEqual((movement.delta, movement.balance_after), (3, 3))

    def test_purchase_is_idempotent_and_refuses_the_same_key_with_other_content(self):
        key = uuid.uuid4()
        data = dict(idempotency_key=key, supply_id=self.box.id, quantity=2, unit_cost=Decimal("5"),
                    occurred_on=timezone.localdate())
        first = create_supply_receipt(data=data, actor=self.user)
        again = create_supply_receipt(data=data, actor=self.user)
        self.assertEqual(first.pk, again.pk)
        self.assertEqual(self.balance(), 2)
        with self.assertRaises(ValidationError):
            create_supply_receipt(data={**data, "quantity": 9}, actor=self.user)

    def test_filament_purchase_updates_the_roll_price(self):
        self.buy(supply=self.filament, quantity=1, cost="89.90")
        self.filament.refresh_from_db()
        self.assertEqual(self.filament.roll_price, Decimal("89.90"))
        self.assertEqual(self.filament.price_per_kg, Decimal("89.90"))

    def test_non_filament_purchase_leaves_prices_alone(self):
        self.buy()
        self.box.refresh_from_db()
        self.assertIsNone(self.box.roll_price)

    # ---- pagamento ----
    def test_paying_creates_one_cash_outflow_once(self):
        receipt = self.buy(quantity=4, cost="25.00")
        pay_supply_receipt(receipt_id=receipt.id, occurred_on=timezone.localdate(), actor=self.user)
        pay_supply_receipt(receipt_id=receipt.id, occurred_on=timezone.localdate(), actor=self.user)
        entry = CashEntry.objects.get()
        self.assertEqual((entry.direction, entry.amount, entry.supply_receipt_id), ("out", Decimal("100.00"), receipt.id))
        self.assertIn("Insumo: Caixa pequena", entry.description)
        receipt.refresh_from_db()
        self.assertIsNotNone(receipt.paid_at)

    def test_payment_date_cannot_be_in_the_future(self):
        receipt = self.buy()
        with self.assertRaises(ValidationError):
            pay_supply_receipt(
                receipt_id=receipt.id, occurred_on=timezone.localdate() + timezone.timedelta(days=1), actor=self.user
            )
        self.assertEqual(CashEntry.objects.count(), 0)

    # ---- cancelamento ----
    def test_cancel_restores_the_balance_keeps_the_record_and_leaves_no_cash_when_unpaid(self):
        adjust_supply_stock(supply_id=self.box.id, delta=5, reason="Inicial", actor=self.user)
        receipt = self.buy(quantity=3)
        cancel_supply_receipt(receipt_id=receipt.id, actor=self.user)
        receipt.refresh_from_db()
        self.assertEqual((receipt.status, self.balance(), CashEntry.objects.count()), ("cancelled", 5, 0))
        self.assertIsNotNone(receipt.cancelled_at)
        self.assertEqual(SupplyReceipt.objects.count(), 1)
        last = SupplyMovement.objects.order_by("-created_at", "-id").first()
        self.assertEqual((last.delta, last.balance_after), (-3, 5))
        self.assertIsNone(last.receipt_id)

    def test_cancel_paid_purchase_refunds_the_cash_only_once(self):
        receipt = self.buy(quantity=2, cost="50.00")
        pay_supply_receipt(receipt_id=receipt.id, occurred_on=timezone.localdate(), actor=self.user)
        cancel_supply_receipt(receipt_id=receipt.id, actor=self.user)
        cancel_supply_receipt(receipt_id=receipt.id, actor=self.user)
        entries = {e.direction: e for e in CashEntry.objects.all()}
        self.assertEqual(entries["in"].amount, Decimal("100.00"))
        self.assertEqual(entries["in"].refund_of_supply_receipt_id, receipt.id)
        self.assertEqual(CashEntry.objects.count(), 2)
        self.assertEqual(SupplyMovement.objects.filter(supply=self.box).count(), 2)

    def test_cancel_is_refused_after_another_movement_and_nothing_changes(self):
        receipt = self.buy(quantity=5)
        adjust_supply_stock(supply_id=self.box.id, delta=-1, reason="Usei 1", actor=self.user)
        with self.assertRaises(ValidationError) as caught:
            cancel_supply_receipt(receipt_id=receipt.id, actor=self.user)
        self.assertIn("receipt", caught.exception.message_dict)
        receipt.refresh_from_db()
        self.assertEqual((receipt.status, self.balance()), ("confirmed", 4))
        newer = self.buy(quantity=1)
        with self.assertRaises(ValidationError):
            cancel_supply_receipt(receipt_id=receipt.id, actor=self.user)
        cancel_supply_receipt(receipt_id=newer.id, actor=self.user)  # a mais recente ainda pode
        self.assertEqual(self.balance(), 4)

    def test_cancelled_purchase_cannot_be_paid(self):
        receipt = self.buy()
        cancel_supply_receipt(receipt_id=receipt.id, actor=self.user)
        with self.assertRaises(ValidationError) as caught:
            pay_supply_receipt(receipt_id=receipt.id, occurred_on=timezone.localdate(), actor=self.user)
        self.assertIn("status", caught.exception.message_dict)
        self.assertEqual(CashEntry.objects.count(), 0)

    def test_cancel_brings_the_roll_price_back_only_if_it_was_not_edited(self):
        first = self.buy(supply=self.filament, quantity=1, cost="89.90")
        cancel_supply_receipt(receipt_id=first.id, actor=self.user)
        self.filament.refresh_from_db()
        self.assertEqual(self.filament.roll_price, Decimal("100.00"))
        second = self.buy(supply=self.filament, quantity=1, cost="80.00")
        Supply.objects.filter(pk=self.filament.pk).update(roll_price=Decimal("95.00"))  # o dono editou
        cancel_supply_receipt(receipt_id=second.id, actor=self.user)
        self.filament.refresh_from_db()
        self.assertEqual(self.filament.roll_price, Decimal("95.00"))


class SupplyStockApiTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("api-supplier")
        self.client = APIClient()
        self.client.force_authenticate(self.admin)
        self.category, _ = SupplyCategory.objects.get_or_create(name="Embalagens")
        self.box = self.client.post(
            "/api/v1/supplies/", {"category": str(self.category.pk), "name": "Caixa média"}, format="json"
        ).json()

    def receipt_body(self, **extra):
        return {
            "idempotency_key": str(uuid.uuid4()),
            "supply_id": self.box["id"],
            "quantity": 10,
            "unit_cost": "3.00",
            "occurred_on": str(timezone.localdate()),
            **extra,
        }

    def test_new_supply_starts_with_zero_and_the_list_shows_the_balance(self):
        self.assertEqual(self.box["quantity"], 0)
        bought = self.client.post("/api/v1/supply-receipts/", self.receipt_body(), format="json")
        self.assertEqual(bought.status_code, 201)
        listed = self.client.get("/api/v1/supplies/").json()["results"]
        self.assertEqual([s["quantity"] for s in listed], [10])

    def test_baixa_and_ajuste_go_through_the_movements_endpoint(self):
        self.client.post("/api/v1/supply-receipts/", self.receipt_body(), format="json")
        baixa = self.client.post(
            "/api/v1/supply-movements/", {"supply": self.box["id"], "delta": -3, "reason": "Usei em 3 envios"}, format="json"
        )
        self.assertEqual(baixa.status_code, 201)
        self.assertEqual(baixa.json()["balance_after"], 7)
        too_much = self.client.post(
            "/api/v1/supply-movements/", {"supply": self.box["id"], "delta": -99, "reason": "Erro"}, format="json"
        )
        self.assertEqual(too_much.status_code, 400)
        history = self.client.get(f"/api/v1/supply-movements/?supply={self.box['id']}").json()["results"]
        self.assertEqual([m["delta"] for m in history], [-3, 10])

    def test_pay_and_cancel_through_the_api(self):
        receipt = self.client.post("/api/v1/supply-receipts/", self.receipt_body(), format="json").json()
        paid = self.client.post(
            f"/api/v1/supply-receipts/{receipt['id']}/pay/", {"occurred_on": str(timezone.localdate())}, format="json"
        )
        self.assertEqual(paid.status_code, 200)
        self.assertIsNotNone(paid.json()["paid_at"])
        cancelled = self.client.post(f"/api/v1/supply-receipts/{receipt['id']}/cancel/", {}, format="json")
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.json()["status"], "cancelled")
        self.assertNotIn("request_hash", cancelled.json())
        self.assertEqual(self.client.get("/api/v1/supplies/").json()["results"][0]["quantity"], 0)

    def test_cancel_refusal_is_a_400_with_the_receipt_message(self):
        receipt = self.client.post("/api/v1/supply-receipts/", self.receipt_body(), format="json").json()
        self.client.post(
            "/api/v1/supply-movements/", {"supply": self.box["id"], "delta": -1, "reason": "Usei"}, format="json"
        )
        response = self.client.post(f"/api/v1/supply-receipts/{receipt['id']}/cancel/", {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("receipt", response.json()["errors"])

    def test_future_date_and_inactive_supply_are_refused(self):
        future = self.client.post(
            "/api/v1/supply-receipts/",
            self.receipt_body(occurred_on=str(timezone.localdate() + timezone.timedelta(days=2))),
            format="json",
        )
        self.assertEqual(future.status_code, 400)
        self.client.patch(f"/api/v1/supplies/{self.box['id']}/", {"active": False}, format="json")
        inactive = self.client.post("/api/v1/supply-receipts/", self.receipt_body(), format="json")
        self.assertEqual(inactive.status_code, 400)

    def test_permissions_are_required_for_each_action(self):
        limited = get_user_model().objects.create_user("supplier-limited", password="x")
        client = APIClient()
        client.force_authenticate(limited)
        self.assertEqual(client.get("/api/v1/supply-movements/").status_code, 403)
        self.assertEqual(client.post("/api/v1/supply-receipts/", self.receipt_body(), format="json").status_code, 403)
        self.assertEqual(SupplyReceipt.objects.count(), 0)


class SupplyConcurrencyTests(TransactionTestCase):
    def test_concurrent_purchase_payment_and_baixa(self):
        if connection.vendor != "postgresql":
            self.skipTest("Exige PostgreSQL real; executado no CI.")
        user = get_user_model().objects.create_user("supplier-threads")
        category = SupplyCategory.objects.create(name="Embalagens concorrência")
        supply = Supply.objects.create(category=category, name="Caixa concorrente")
        data = dict(
            idempotency_key=uuid.uuid4(),
            supply_id=supply.id,
            quantity=1,
            unit_cost=Decimal("10"),
            occurred_on=timezone.localdate(),
        )

        def submit(_):
            close_old_connections()
            try:
                return create_supply_receipt(data=data, actor=user).id
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            ids = list(pool.map(submit, range(2)))
        self.assertEqual(ids[0], ids[1])
        self.assertEqual(SupplyStock.objects.get(supply=supply).quantity, 1)

        def pay(_):
            close_old_connections()
            try:
                pay_supply_receipt(receipt_id=ids[0], occurred_on=timezone.localdate(), actor=user)
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(pay, range(2)))
        self.assertEqual(CashEntry.objects.count(), 1)

        def baixa(_):
            close_old_connections()
            try:
                adjust_supply_stock(supply_id=supply.id, delta=-1, reason="Usei", actor=user)
                return True
            except ValidationError:
                return False
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(baixa, range(2)))
        self.assertEqual(sorted(results), [False, True])  # só uma das duas baixas cabe no saldo de 1
        self.assertEqual(SupplyStock.objects.get(supply=supply).quantity, 0)
