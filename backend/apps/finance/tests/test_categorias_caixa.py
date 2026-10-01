import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.catalog.models import Product
from apps.finance.domain.categories import direction_fits, origin_of, system_key_for
from apps.finance.models import CashCategory, CashEntry, system_category
from apps.inventory.models import Stock
from apps.inventory.services import adjust_stock, cancel_receipt, create_receipt, pay_receipt
from apps.sales.services import cancel_sale, create_sale, receive_sale
from apps.supplies.models import Supply, SupplyCategory
from apps.supplies.services import cancel_supply_receipt, create_supply_receipt, pay_supply_receipt


class CashCategoryDomainTests(SimpleTestCase):
    def test_origin_of_each_link(self):
        self.assertEqual(origin_of(direction="in", sale=True), "sale")
        self.assertEqual(origin_of(direction="out", sale=True), "sale_refund")
        self.assertEqual(origin_of(direction="out", receipt=True), "purchase")
        self.assertEqual(origin_of(direction="in", refund_of_receipt=True), "purchase_refund")
        self.assertEqual(origin_of(direction="out", supply_receipt=True), "supply")
        self.assertEqual(origin_of(direction="in", refund_of_supply_receipt=True), "supply_refund")
        self.assertEqual(origin_of(direction="out"), "manual")

    def test_manual_without_category_falls_to_unclassified(self):
        self.assertEqual(system_key_for("manual"), "unclassified")
        self.assertEqual(system_key_for("supply"), "supply_purchase")

    def test_direction_fits(self):
        self.assertTrue(direction_fits("out", "out"))
        self.assertTrue(direction_fits("both", "in"))
        self.assertFalse(direction_fits("in", "out"))


class CashCategoryApiTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("cash-admin", password="test-pass")
        self.client = APIClient()
        self.client.force_authenticate(self.admin)
        self.expense = CashCategory.objects.create(name="Impostos teste", direction="out", counts_in_result=True)
        self.income = CashCategory.objects.create(name="Receita teste", direction="in", counts_in_result=True)

    def entry(self, **extra):
        body = {
            "direction": "out",
            "amount": "50.00",
            "description": "Conta",
            "occurred_on": str(timezone.localdate()),
            "category": str(self.expense.pk),
            **extra,
        }
        return self.client.post("/api/v1/cash/", body, format="json")

    # ---- categorias ----
    def test_create_category_with_direction_and_unique_name_ignoring_accent(self):
        created = self.client.post(
            "/api/v1/cash-categories/", {"name": "  Água   e esgoto ", "direction": "out"}, format="json"
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["name"], "Água e esgoto")
        self.assertTrue(created.json()["counts_in_result"])
        self.assertFalse(created.json()["is_system"])
        clash = self.client.post("/api/v1/cash-categories/", {"name": "ÁGUA E ESGOTO", "direction": "out"}, format="json")
        self.assertEqual(clash.status_code, 400)

    def test_system_categories_are_read_only_and_flagged(self):
        system = system_category("unclassified")
        edit = self.client.patch(f"/api/v1/cash-categories/{system.pk}/", {"name": "Outro nome"}, format="json")
        self.assertEqual(edit.status_code, 400)
        listed = {c["name"]: c for c in self.client.get("/api/v1/cash-categories/").json()["results"]}
        self.assertTrue(listed["A classificar"]["is_system"])
        only_user = self.client.get("/api/v1/cash-categories/?system=false").json()["results"]
        self.assertTrue(all(not c["is_system"] for c in only_user))
        only_system = self.client.get("/api/v1/cash-categories/?system=true").json()["results"]
        self.assertTrue(only_system and all(c["is_system"] for c in only_system))

    def test_direction_locks_after_the_first_entry_and_no_delete(self):
        self.assertEqual(self.entry().status_code, 201)
        locked = self.client.patch(f"/api/v1/cash-categories/{self.expense.pk}/", {"direction": "in"}, format="json")
        self.assertEqual(locked.status_code, 400)
        self.assertEqual(self.client.delete(f"/api/v1/cash-categories/{self.expense.pk}/").status_code, 405)
        flag = self.client.patch(
            f"/api/v1/cash-categories/{self.expense.pk}/", {"counts_in_result": False}, format="json"
        )
        self.assertEqual(flag.status_code, 200)  # a marca pode mudar: vale também para o passado
        row = next(c for c in self.client.get("/api/v1/cash-categories/").json()["results"] if c["id"] == str(self.expense.pk))
        self.assertEqual(row["entries_count"], 1)

    # ---- lançamento manual ----
    def test_manual_entry_needs_a_valid_category(self):
        missing = self.entry(category=None)
        self.assertEqual(missing.status_code, 400)
        self.assertIn("category", missing.json()["errors"])
        wrong_direction = self.entry(category=str(self.income.pk))
        self.assertEqual(wrong_direction.status_code, 400)
        system = self.entry(category=str(system_category("unclassified").pk))
        self.assertEqual(system.status_code, 400)
        CashCategory.objects.filter(pk=self.expense.pk).update(active=False)
        self.assertEqual(self.entry().status_code, 400)
        self.assertEqual(CashEntry.objects.count(), 0)

    def test_manual_entry_is_saved_with_category_and_origin(self):
        response = self.entry()
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual((body["category_name"], body["origin"]), ("Impostos teste", "manual"))

    def test_both_direction_category_serves_entries_and_exits(self):
        both = CashCategory.objects.create(name="Ajustes teste", direction="both")
        for direction in ("in", "out"):
            self.assertEqual(self.entry(direction=direction, category=str(both.pk)).status_code, 201)

    # ---- reclassificar ----
    def test_reclassify_changes_only_the_category_of_a_manual_entry(self):
        created = self.entry().json()
        other = CashCategory.objects.create(name="Outra saída teste", direction="out")
        ok = self.client.patch(f"/api/v1/cash/{created['id']}/", {"category": str(other.pk)}, format="json")
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json()["category_name"], "Outra saída teste")
        for field, value in (("amount", "1.00"), ("description", "Outra"), ("direction", "in"), ("occurred_on", "2020-01-01")):
            bad = self.client.patch(f"/api/v1/cash/{created['id']}/", {field: value}, format="json")
            self.assertEqual(bad.status_code, 400, field)
        entry = CashEntry.objects.get(pk=created["id"])
        self.assertEqual((entry.amount, entry.description, entry.direction), (Decimal("50.00"), "Conta", "out"))

    def test_reclassify_rules(self):
        legacy = CashEntry.objects.create(
            direction="out", amount=Decimal("10"), description="Antigo", occurred_on=timezone.localdate(), actor=self.admin
        )
        self.assertEqual(legacy.category.system_key, "unclassified")
        wrong = self.client.patch(f"/api/v1/cash/{legacy.pk}/", {"category": str(self.income.pk)}, format="json")
        self.assertEqual(wrong.status_code, 400)
        to_system = self.client.patch(
            f"/api/v1/cash/{legacy.pk}/", {"category": str(system_category("purchase").pk)}, format="json"
        )
        self.assertEqual(to_system.status_code, 400)
        ok = self.client.patch(f"/api/v1/cash/{legacy.pk}/", {"category": str(self.expense.pk)}, format="json")
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(self.client.put(f"/api/v1/cash/{legacy.pk}/", {}, format="json").status_code, 405)

    def test_summary_totals_by_category(self):
        self.entry()
        self.entry(amount="25.00")
        self.entry(direction="in", category=str(self.income.pk), amount="100.00")
        rows = {r["category_name"]: r for r in self.client.get("/api/v1/cash/summary/").json()}
        self.assertEqual((rows["Impostos teste"]["out_total"], rows["Impostos teste"]["entries"]), ("75.00", 2))
        self.assertEqual(rows["Receita teste"]["in_total"], "100.00")
        self.assertFalse(rows["Receita teste"]["is_system"])

    def test_category_endpoints_need_permissions(self):
        limited = get_user_model().objects.create_user("cash-limited", password="x")
        client = APIClient()
        client.force_authenticate(limited)
        self.assertEqual(client.get("/api/v1/cash-categories/").status_code, 403)
        self.assertEqual(client.get("/api/v1/cash/summary/").status_code, 403)
        self.assertEqual(client.patch(f"/api/v1/cash/{uuid.uuid4()}/", {}, format="json").status_code, 403)


class AutomaticCategoryTests(TestCase):
    """Todo caminho que cria lançamento automático recebe a categoria do sistema pela origem."""

    def setUp(self):
        self.user = get_user_model().objects.create_superuser("auto-cat")
        self.product = Product.objects.create(sku="AUTO-CAT", name="Controle")
        Stock.objects.get_or_create(product=self.product)
        adjust_stock(product_id=self.product.id, delta=20, reason="Inicial", actor=self.user, unit_cost=Decimal("10"))

    def names(self):
        return sorted(CashEntry.objects.values_list("category__name", flat=True))

    def test_sale_received_and_refunded(self):
        sale = create_sale(
            data=dict(
                idempotency_key=uuid.uuid4(),
                channel="direct",
                items=[dict(product_id=self.product.id, quantity=1, unit_price=Decimal("30"))],
            ),
            actor=self.user,
        )
        receive_sale(sale_id=sale.id, actor=self.user)
        cancel_sale(sale_id=sale.id, actor=self.user)
        self.assertEqual(self.names(), ["Estorno de venda", "Venda recebida"])

    def test_product_purchase_paid_and_refunded(self):
        receipt = create_receipt(
            data=dict(
                idempotency_key=uuid.uuid4(), product_id=self.product.id, kind="purchase", quantity=2,
                unit_cost=Decimal("5"), occurred_on=timezone.localdate(),
            ),
            actor=self.user,
        )
        pay_receipt(receipt_id=receipt.id, occurred_on=timezone.localdate(), actor=self.user)
        cancel_receipt(receipt_id=receipt.id, actor=self.user)
        self.assertEqual(self.names(), ["Compra de produtos", "Estorno de compra de produtos"])

    def test_supply_purchase_paid_and_refunded(self):
        category, _ = SupplyCategory.objects.get_or_create(name="Embalagens")
        supply = Supply.objects.create(category=category, name="Caixa", unit="pacote")
        receipt = create_supply_receipt(
            data=dict(
                idempotency_key=uuid.uuid4(), supply_id=supply.id, quantity=2, unit_cost=Decimal("5"),
                occurred_on=timezone.localdate(),
            ),
            actor=self.user,
        )
        pay_supply_receipt(receipt_id=receipt.id, occurred_on=timezone.localdate(), actor=self.user)
        cancel_supply_receipt(receipt_id=receipt.id, actor=self.user)
        self.assertEqual(self.names(), ["Compra de insumos", "Estorno de compra de insumos"])
