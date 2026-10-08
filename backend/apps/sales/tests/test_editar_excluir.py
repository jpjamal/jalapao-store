import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Product
from apps.finance.models import CashEntry
from apps.integrations.services.mercado_livre.pedidos import _venda
from apps.inventory.models import Stock
from apps.inventory.services import adjust_stock
from apps.sales.models import SaleRevision
from apps.sales.services import create_sale, delete_sale, edit_sale, receive_sale
from apps.supplies.models import Supply, SupplyCategory, SupplyStock
from apps.supplies.services import adjust_supply_stock


class SaleChangeBase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("sale-editor")
        self.product = Product.objects.create(name="Controle 8BitDo", cost_price=Decimal("10"))
        adjust_stock(
            product_id=self.product.id,
            delta=5,
            reason="Estoque inicial",
            actor=self.user,
            unit_cost=Decimal("10"),
        )

    def sell(self, **extra):
        data = {
            "idempotency_key": uuid.uuid4(),
            "channel": "direct",
            "reference": "Venda original",
            "discount": Decimal("2"),
            "platform_fee": Decimal("3"),
            "shipping_cost": Decimal("5"),
            "items": [{"product_id": self.product.id, "quantity": 2, "unit_price": Decimal("25")}],
            **extra,
        }
        return create_sale(data=data, actor=self.user)

    def edit_data(self, sale, **extra):
        return {
            "request_key": uuid.uuid4(),
            "expected_updated_at": sale.updated_at,
            "channel": "site",
            "reference": "Venda corrigida",
            "discount": Decimal("1"),
            "platform_fee": Decimal("2"),
            "shipping_cost": Decimal("3"),
            "items": [{"id": sale.items.get().id, "unit_price": Decimal("30")}],
            **extra,
        }

    def product_balance(self):
        return Stock.objects.get(product=self.product).quantity


class EditSaleTests(SaleChangeBase):
    def test_edit_recalculates_totals_without_touching_stock_or_cost(self):
        sale = self.sell()

        changed = edit_sale(sale_id=sale.id, data=self.edit_data(sale), actor=self.user)

        item = changed.items.get()
        self.assertEqual((changed.channel, changed.reference), ("site", "Venda corrigida"))
        self.assertEqual((item.product_id, item.quantity, item.unit_price), (self.product.id, 2, Decimal("30")))
        self.assertEqual(
            (changed.gross, changed.net, changed.cost_total, changed.profit),
            (Decimal("60"), Decimal("54"), Decimal("20"), Decimal("34")),
        )
        self.assertEqual(self.product_balance(), 3)
        self.assertEqual(CashEntry.objects.count(), 0)
        revision = SaleRevision.objects.get(sale=sale)
        self.assertEqual(revision.action, "edit")
        self.assertEqual(revision.before["net"], "40.00")
        self.assertEqual(revision.after["net"], "54.00")

    def test_received_sale_records_only_each_difference_and_cancel_balances_cash(self):
        sale = self.sell()
        receive_sale(sale_id=sale.id, actor=self.user)
        sale.refresh_from_db()

        first = self.edit_data(sale, discount=Decimal("0"), platform_fee=Decimal("0"), shipping_cost=Decimal("0"))
        changed = edit_sale(sale_id=sale.id, data=first, actor=self.user)
        self.assertEqual(changed.net, Decimal("60"))

        second = self.edit_data(changed, discount=Decimal("15"), platform_fee=Decimal("5"), shipping_cost=Decimal("0"))
        changed = edit_sale(sale_id=sale.id, data=second, actor=self.user)
        self.assertEqual(changed.net, Decimal("40"))

        entries = list(CashEntry.objects.filter(sale=sale).order_by("created_at"))
        self.assertEqual([(row.direction, row.amount) for row in entries], [
            ("in", Decimal("40")), ("in", Decimal("20")), ("out", Decimal("20")),
        ])
        self.assertEqual([row.origin for row in entries], ["sale", "sale_adjustment", "sale_adjustment"])

        delete_sale(sale_id=sale.id, actor=self.user)
        entries = CashEntry.objects.filter(sale=sale)
        balance = sum((row.amount if row.direction == "in" else -row.amount) for row in entries)
        self.assertEqual(balance, Decimal("0"))
        self.assertEqual(entries.filter(direction="out", sale_revision__isnull=True).get().amount, Decimal("40"))

    def test_same_request_is_idempotent_and_changed_payload_is_rejected(self):
        sale = self.sell()
        receive_sale(sale_id=sale.id, actor=self.user)
        sale.refresh_from_db()
        data = self.edit_data(sale)

        first = edit_sale(sale_id=sale.id, data=data, actor=self.user)
        again = edit_sale(sale_id=sale.id, data=data, actor=self.user)

        self.assertEqual(first.id, again.id)
        self.assertEqual(SaleRevision.objects.filter(sale=sale).count(), 1)
        self.assertEqual(CashEntry.objects.filter(sale_revision__isnull=False).count(), 1)
        with self.assertRaises(ValidationError):
            edit_sale(sale_id=sale.id, data={**data, "reference": "Outro conteúdo"}, actor=self.user)

    def test_stale_version_and_invalid_total_roll_back_everything(self):
        sale = self.sell()
        stale = sale.updated_at
        sale.reference = "Mudança paralela"
        sale.save(update_fields=["reference", "updated_at"])
        sale.refresh_from_db()
        with self.assertRaises(ValidationError):
            edit_sale(sale_id=sale.id, data={**self.edit_data(sale), "expected_updated_at": stale}, actor=self.user)

        bad = self.edit_data(sale, discount=Decimal("100"))
        with self.assertRaises(ValidationError):
            edit_sale(sale_id=sale.id, data=bad, actor=self.user)
        sale.refresh_from_db()
        self.assertEqual((sale.reference, sale.net), ("Mudança paralela", Decimal("40")))
        self.assertEqual(sale.items.get().unit_price, Decimal("25"))
        self.assertFalse(SaleRevision.objects.exists())

    def test_import_origin_survives_channel_edit_and_delete(self):
        sale = self.sell()
        sale.external_channel = "mercado_livre"
        sale.external_id = "2000001"
        sale.save(update_fields=["external_channel", "external_id", "updated_at"])
        sale.refresh_from_db()

        edit_sale(sale_id=sale.id, data=self.edit_data(sale, channel="other"), actor=self.user)
        self.assertEqual(_venda("2000001").id, sale.id)
        delete_sale(sale_id=sale.id, actor=self.user)
        self.assertEqual(_venda("2000001").id, sale.id)


class DeleteSaleTests(SaleChangeBase):
    def test_delete_hides_sale_and_restores_products_supplies_and_cash_once(self):
        category, _ = SupplyCategory.objects.get_or_create(name="Embalagens")
        box = Supply.objects.create(category=category, name="Caixa pequena")
        adjust_supply_stock(supply_id=box.id, delta=4, reason="Estoque inicial", actor=self.user)
        sale = self.sell(supplies=[{"supply_id": box.id, "quantity": 2}])
        receive_sale(sale_id=sale.id, actor=self.user)

        delete_sale(sale_id=sale.id, actor=self.user)
        delete_sale(sale_id=sale.id, actor=self.user)

        sale.refresh_from_db()
        self.assertEqual(sale.status, "cancelled")
        self.assertIsNotNone(sale.deleted_at)
        self.assertEqual(self.product_balance(), 5)
        self.assertEqual(SupplyStock.objects.get(supply=box).quantity, 4)
        self.assertEqual(SaleRevision.objects.filter(sale=sale, action="delete").count(), 1)
        self.assertEqual(CashEntry.objects.filter(sale=sale).count(), 2)


class SaleChangeApiTests(SaleChangeBase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def payload(self, sale, **extra):
        data = self.edit_data(sale)
        data.update(extra)
        return {
            **data,
            "request_key": str(data["request_key"]),
            "expected_updated_at": data["expected_updated_at"].isoformat(),
            "items": [{"id": str(row["id"]), "unit_price": str(row["unit_price"])} for row in data["items"]],
            "discount": str(data["discount"]),
            "platform_fee": str(data["platform_fee"]),
            "shipping_cost": str(data["shipping_cost"]),
        }

    def limited_client(self, *codenames):
        user = get_user_model().objects.create_user(f"limited-{uuid.uuid4().hex[:8]}")
        user.user_permissions.set(Permission.objects.filter(codename__in=codenames))
        client = APIClient()
        client.force_authenticate(user)
        return client

    def test_patch_is_strict_and_list_omits_deleted_sale(self):
        sale = self.sell()
        bad = self.client.patch(
            f"/api/v1/sales/{sale.id}/",
            {**self.payload(sale), "quantity": 99},
            format="json",
        )
        self.assertEqual(bad.status_code, 400)

        changed = self.client.patch(f"/api/v1/sales/{sale.id}/", self.payload(sale), format="json")
        self.assertEqual(changed.status_code, 200, changed.content)
        self.assertEqual(changed.json()["channel"], "site")

        deleted = self.client.delete(f"/api/v1/sales/{sale.id}/")
        self.assertEqual(deleted.status_code, 204, deleted.content)
        self.assertEqual(self.client.get("/api/v1/sales/").json()["count"], 0)

    def test_delete_requires_delete_sale_permission(self):
        sale = self.sell()
        client = self.limited_client(
            "view_sale", "change_sale", "add_movement", "add_cashentry", "add_supplymovement"
        )
        response = client.delete(f"/api/v1/sales/{sale.id}/")
        self.assertEqual(response.status_code, 403)
        sale.refresh_from_db()
        self.assertIsNone(sale.deleted_at)

    def test_received_patch_requires_cash_permission(self):
        sale = self.sell()
        receive_sale(sale_id=sale.id, actor=self.user)
        sale.refresh_from_db()
        client = self.limited_client("view_sale", "change_sale")
        response = client.patch(f"/api/v1/sales/{sale.id}/", self.payload(sale), format="json")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(SaleRevision.objects.exists())
