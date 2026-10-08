import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.finance.models import CashCategory, CashEntry
from apps.supplies.models import Supply, SupplyCategory
from apps.supplies.services import cancel_supply_receipt, create_supply_receipt, pay_supply_receipt


class BusinessResultTests(TestCase):
    """resultado = lucro real + entradas manuais que contam − saídas manuais que contam − despesa com insumos
    (só das categorias de insumo que contam). Nada disso mexe no saldo do Caixa."""

    def setUp(self):
        self.user = get_user_model().objects.create_superuser("result-admin", password="test-pass")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.taxes = CashCategory.objects.create(name="Impostos r", direction="out", counts_in_result=True)
        self.energy = CashCategory.objects.create(name="Energia r", direction="out", counts_in_result=False)
        self.loan = CashCategory.objects.create(name="Empréstimo r", direction="in", counts_in_result=False)
        self.extra = CashCategory.objects.create(name="Outras receitas r", direction="in", counts_in_result=True)
        self.withdrawal = CashCategory.objects.create(name="Retirada r", direction="out", counts_in_result=False)

    def cash(self, category, direction, amount):
        return CashEntry.objects.create(
            direction=direction, amount=Decimal(amount), description="Teste", occurred_on=timezone.localdate(),
            actor=self.user, category=category,
        )

    def dashboard(self):
        return self.client.get("/api/v1/dashboard/").json()

    def result(self):
        return Decimal(self.dashboard()["business_result"])

    def test_without_anything_the_result_is_zero(self):
        body = self.dashboard()
        self.assertEqual((Decimal(body["business_result"]), body["unclassified_count"]), (Decimal(0), 0))

    def test_only_categories_that_count_enter_the_result(self):
        self.cash(self.taxes, "out", "100")  # despesa que conta
        self.cash(self.energy, "out", "40")  # categoria que não conta
        self.cash(self.loan, "in", "500")  # empréstimo: só saldo
        self.cash(self.withdrawal, "out", "200")  # retirada do dono: só saldo
        self.cash(self.extra, "in", "30")  # receita que conta
        self.assertEqual(self.result(), Decimal("-70"))
        self.assertEqual(Decimal(self.dashboard()["cash_balance"]), Decimal("190"))  # 500 + 30 - 100 - 40 - 200

    def test_changing_counts_in_result_changes_the_past_too(self):
        self.cash(self.energy, "out", "40")
        self.assertEqual(self.result(), Decimal(0))
        self.client.patch(f"/api/v1/cash-categories/{self.energy.pk}/", {"counts_in_result": True}, format="json")
        self.assertEqual(self.result(), Decimal("-40"))

    def test_unclassified_entries_stay_out_of_the_result_and_are_counted(self):
        CashEntry.objects.create(
            direction="out", amount=Decimal("90"), description="Antigo", occurred_on=timezone.localdate(), actor=self.user
        )
        body = self.dashboard()
        self.assertEqual((Decimal(body["business_result"]), body["unclassified_count"]), (Decimal(0), 1))
        old = CashEntry.objects.get()
        self.client.patch(f"/api/v1/cash/{old.pk}/", {"category": str(self.taxes.pk)}, format="json")
        body = self.dashboard()
        self.assertEqual((Decimal(body["business_result"]), body["unclassified_count"]), (Decimal("-90"), 0))

    def test_system_categories_do_not_count_even_if_the_flag_were_on(self):
        entry = CashEntry.objects.create(
            direction="in", amount=Decimal("50"), description="Antigo", occurred_on=timezone.localdate(), actor=self.user
        )
        CashCategory.objects.filter(pk=entry.category_id).update(counts_in_result=True)
        self.assertEqual(self.result(), Decimal(0))


class SupplyExpenseTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("supply-expense", password="test-pass")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.counts = SupplyCategory.objects.create(name="Embalagens r", counts_as_expense=True)
        self.free = SupplyCategory.objects.create(name="Acabamento r", counts_as_expense=False)
        self.box = Supply.objects.create(category=self.counts, name="Caixa r", unit="pacote")
        self.varnish = Supply.objects.create(category=self.free, name="Verniz r", unit="frasco")

    def buy_and_pay(self, supply, quantity, cost):
        receipt = create_supply_receipt(
            data=dict(
                idempotency_key=uuid.uuid4(), supply_id=supply.id, quantity=quantity, unit_cost=Decimal(cost),
                occurred_on=timezone.localdate(),
            ),
            actor=self.user,
        )
        pay_supply_receipt(receipt_id=receipt.id, occurred_on=timezone.localdate(), actor=self.user)
        return receipt

    def result(self):
        return Decimal(self.client.get("/api/v1/dashboard/").json()["business_result"])

    def test_only_supplies_of_categories_that_count_are_an_expense(self):
        self.buy_and_pay(self.box, 2, "50")  # R$ 100 que conta
        self.buy_and_pay(self.varnish, 1, "200")  # R$ 200 que não conta
        self.assertEqual(self.result(), Decimal("-100"))
        self.assertEqual(Decimal(self.client.get("/api/v1/dashboard/").json()["cash_balance"]), Decimal("-300"))

    def test_unpaid_purchase_is_not_an_expense_yet(self):
        create_supply_receipt(
            data=dict(
                idempotency_key=uuid.uuid4(), supply_id=self.box.id, quantity=1, unit_cost=Decimal("80"),
                occurred_on=timezone.localdate(),
            ),
            actor=self.user,
        )
        self.assertEqual(self.result(), Decimal(0))

    def test_refund_reduces_the_expense(self):
        receipt = self.buy_and_pay(self.box, 2, "50")
        self.assertEqual(self.result(), Decimal("-100"))
        cancel_supply_receipt(receipt_id=receipt.id, actor=self.user)
        self.assertEqual(self.result(), Decimal(0))

    def test_switching_the_category_option_preserves_the_past_and_applies_to_future_purchases(self):
        historical = self.buy_and_pay(self.varnish, 1, "200")
        self.assertEqual(self.result(), Decimal(0))
        edited = self.client.patch(
            f"/api/v1/supply-categories/{self.free.pk}/", {"counts_as_expense": True}, format="json"
        )
        self.assertEqual(edited.status_code, 200)
        self.assertTrue(edited.json()["counts_as_expense"])
        historical.refresh_from_db()
        self.assertFalse(historical.counts_as_expense_snapshot)
        self.assertEqual(self.result(), Decimal(0))

        future = self.buy_and_pay(self.varnish, 1, "30")
        self.assertTrue(future.counts_as_expense_snapshot)
        self.assertEqual(self.result(), Decimal("-30"))

    def test_moving_a_supply_to_another_category_does_not_reclassify_old_purchases(self):
        receipt = self.buy_and_pay(self.box, 2, "50")
        self.assertEqual(self.result(), Decimal("-100"))

        moved = self.client.patch(
            f"/api/v1/supplies/{self.box.pk}/", {"category": str(self.free.pk)}, format="json"
        )
        self.assertEqual(moved.status_code, 200)
        receipt.refresh_from_db()
        self.assertTrue(receipt.counts_as_expense_snapshot)
        self.assertEqual(self.result(), Decimal("-100"))
        cancel_supply_receipt(receipt_id=receipt.id, actor=self.user)
        self.assertEqual(self.result(), Decimal(0))

    def test_new_supply_category_counts_by_default(self):
        created = self.client.post("/api/v1/supply-categories/", {"name": "Nova r"}, format="json")
        self.assertEqual(created.status_code, 201)
        self.assertTrue(created.json()["counts_as_expense"])
