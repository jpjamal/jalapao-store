import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Product
from apps.inventory.models import Stock
from apps.inventory.services import adjust_stock
from apps.sales.models import Sale
from apps.sales.services import cancel_sale, create_sale
from apps.supplies.models import SaleSupply, Supply, SupplyCategory, SupplyMovement, SupplyStock
from apps.supplies.services import adjust_supply_stock


class SuppliesOnSaleTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("sale-supplies")
        self.category, _ = SupplyCategory.objects.get_or_create(name="Embalagens")
        self.box = Supply.objects.create(category=self.category, name="Caixa pequena", unit="pacote")
        self.label = Supply.objects.create(category=self.category, name="Etiqueta", unit="rolo")
        self.product = Product.objects.create(sku="VENDA-INS", name="Controle 8BitDo")
        Stock.objects.get_or_create(product=self.product)
        adjust_stock(product_id=self.product.id, delta=10, reason="Inicial", actor=self.user, unit_cost=Decimal("5"))

    def stock_of(self, supply, quantity):
        adjust_supply_stock(supply_id=supply.id, delta=quantity, reason="Inicial", actor=self.user)

    def balance(self, supply):
        stock = SupplyStock.objects.filter(supply=supply).first()
        return stock.quantity if stock else 0

    def sell(self, supplies=None, quantity=2, key=None):
        data = dict(
            idempotency_key=key or uuid.uuid4(),
            channel="direct",
            items=[dict(product_id=self.product.id, quantity=quantity, unit_price=Decimal("25"))],
        )
        if supplies is not None:
            data["supplies"] = supplies
        return create_sale(data=data, actor=self.user)

    def test_supplies_used_are_taken_from_the_balance_and_linked_to_the_sale(self):
        self.stock_of(self.box, 10)
        self.stock_of(self.label, 5)
        sale = self.sell([{"supply_id": self.box.id, "quantity": 1}, {"supply_id": self.label.id, "quantity": 2}])
        self.assertEqual((self.balance(self.box), self.balance(self.label)), (9, 3))
        lines = {line.supply_name: line for line in sale.supply_lines.all()}
        self.assertEqual((lines["Caixa pequena"].requested, lines["Caixa pequena"].taken), (1, 1))
        self.assertEqual((lines["Etiqueta"].requested, lines["Etiqueta"].taken), (2, 2))
        movement = SupplyMovement.objects.get(sale=sale, supply=self.label)
        self.assertEqual((movement.delta, movement.balance_after, movement.reason), (-2, 3, "Venda confirmada"))

    def test_profit_and_cost_do_not_change_with_supplies(self):
        self.stock_of(self.box, 10)
        plain = self.sell()
        with_supplies = self.sell([{"supply_id": self.box.id, "quantity": 3}])
        self.assertEqual((with_supplies.cost_total, with_supplies.profit), (plain.cost_total, plain.profit))
        self.assertEqual(with_supplies.cost_total, Decimal("10.00"))

    def test_sale_without_supplies_creates_no_supply_lines(self):
        for sale in (self.sell(), self.sell([])):
            self.assertEqual(sale.supply_lines.count(), 0)

    def test_shortfall_does_not_block_the_sale_and_takes_only_what_exists(self):
        self.stock_of(self.box, 3)
        sale = self.sell([{"supply_id": self.box.id, "quantity": 5}])
        line = sale.supply_lines.get()
        self.assertEqual((line.requested, line.taken), (5, 3))
        self.assertEqual(self.balance(self.box), 0)
        self.assertEqual(Sale.objects.count(), 1)
        self.assertEqual(Stock.objects.get(product=self.product).quantity, 8)

    def test_supply_without_any_balance_is_recorded_with_nothing_taken(self):
        sale = self.sell([{"supply_id": self.box.id, "quantity": 2}])
        line = sale.supply_lines.get()
        self.assertEqual((line.requested, line.taken), (2, 0))
        self.assertFalse(SupplyMovement.objects.filter(sale=sale).exists())

    def test_cancelling_returns_exactly_what_was_taken_even_for_an_inactive_supply(self):
        self.stock_of(self.box, 3)
        sale = self.sell([{"supply_id": self.box.id, "quantity": 5}])
        Supply.objects.filter(pk=self.box.pk).update(active=False)
        cancel_sale(sale_id=sale.id, actor=self.user)
        cancel_sale(sale_id=sale.id, actor=self.user)  # repetir não devolve de novo
        self.assertEqual(self.balance(self.box), 3)
        restored = SupplyMovement.objects.filter(sale=sale, delta__gt=0)
        self.assertEqual([(m.delta, m.reason) for m in restored], [(3, "Cancelamento de venda")])

    def test_repeating_the_same_request_does_not_take_twice(self):
        self.stock_of(self.box, 10)
        key = uuid.uuid4()
        first = self.sell([{"supply_id": self.box.id, "quantity": 2}], key=key)
        again = self.sell([{"supply_id": self.box.id, "quantity": 2}], key=key)
        self.assertEqual(first.pk, again.pk)
        self.assertEqual(self.balance(self.box), 8)
        self.assertEqual(SaleSupply.objects.count(), 1)

    def test_invalid_supply_lines_roll_the_whole_sale_back(self):
        self.stock_of(self.box, 10)
        with self.assertRaises(ValidationError):
            self.sell([{"supply_id": self.box.id, "quantity": 1}, {"supply_id": self.box.id, "quantity": 1}])
        with self.assertRaises(ValidationError):
            self.sell([{"supply_id": uuid.uuid4(), "quantity": 1}])
        self.assertEqual(Sale.objects.count(), 0)
        self.assertEqual(Stock.objects.get(product=self.product).quantity, 10)
        self.assertEqual(self.balance(self.box), 10)


class SuppliesOnSaleApiTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("api-sale-supplies")
        self.client = APIClient()
        self.client.force_authenticate(self.admin)
        category, _ = SupplyCategory.objects.get_or_create(name="Embalagens")
        self.box = Supply.objects.create(category=category, name="Caixa API", unit="pacote")
        adjust_supply_stock(supply_id=self.box.id, delta=3, reason="Inicial", actor=self.admin)
        self.product = Product.objects.create(sku="VENDA-API", name="Produto API")
        Stock.objects.get_or_create(product=self.product)
        adjust_stock(product_id=self.product.id, delta=10, reason="Inicial", actor=self.admin, unit_cost=Decimal("5"))

    def body(self, **extra):
        return {
            "idempotency_key": str(uuid.uuid4()),
            "channel": "direct",
            "items": [{"product_id": str(self.product.id), "quantity": 1, "unit_price": "25.00"}],
            **extra,
        }

    def test_sale_response_lists_supplies_and_the_shortfall(self):
        response = self.client.post(
            "/api/v1/sales/", self.body(supplies=[{"supply_id": str(self.box.id), "quantity": 5}]), format="json"
        )
        self.assertEqual(response.status_code, 201)
        line = response.json()["supplies"][0]
        self.assertEqual(
            (line["supply_name"], line["requested"], line["taken"], line["shortfall"]), ("Caixa API", 5, 3, 2)
        )
        listed = self.client.get("/api/v1/sales/").json()["results"][0]
        self.assertEqual(listed["supplies"][0]["shortfall"], 2)

    def test_sale_without_supplies_key_still_works(self):
        response = self.client.post("/api/v1/sales/", self.body(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["supplies"], [])

    def test_bad_supply_input_is_a_400(self):
        for supplies in ([{"supply_id": str(self.box.id), "quantity": 0}], [{"supply_id": "nao-e-uuid", "quantity": 1}]):
            response = self.client.post("/api/v1/sales/", self.body(supplies=supplies), format="json")
            self.assertEqual(response.status_code, 400)
        repeated = self.client.post(
            "/api/v1/sales/",
            self.body(supplies=[{"supply_id": str(self.box.id), "quantity": 1}] * 2),
            format="json",
        )
        self.assertEqual(repeated.status_code, 400)
        self.assertEqual(Sale.objects.count(), 0)

    def limited_client(self, *codenames):
        user = get_user_model().objects.create_user(f"limited-{uuid.uuid4().hex[:6]}", password="x")
        user.user_permissions.set(Permission.objects.filter(codename__in=codenames))
        client = APIClient()
        client.force_authenticate(user)
        return client

    def test_informing_supplies_needs_the_supply_stock_permission(self):
        client = self.limited_client("add_sale", "add_movement")
        with_supplies = client.post(
            "/api/v1/sales/", self.body(supplies=[{"supply_id": str(self.box.id), "quantity": 1}]), format="json"
        )
        self.assertEqual(with_supplies.status_code, 403)
        self.assertEqual(Sale.objects.count(), 0)
        without = client.post("/api/v1/sales/", self.body(), format="json")
        self.assertEqual(without.status_code, 201)

    def test_cancelling_a_sale_that_took_supplies_needs_the_supply_permission(self):
        created = self.client.post(
            "/api/v1/sales/", self.body(supplies=[{"supply_id": str(self.box.id), "quantity": 2}]), format="json"
        ).json()
        client = self.limited_client("view_sale", "change_sale", "add_movement", "add_cashentry", "add_sale")
        refused = client.post(f"/api/v1/sales/{created['id']}/cancel/", {}, format="json")
        self.assertEqual(refused.status_code, 403)
        self.assertEqual(SupplyStock.objects.get(supply=self.box).quantity, 1)
        allowed = self.client.post(f"/api/v1/sales/{created['id']}/cancel/", {}, format="json")
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(SupplyStock.objects.get(supply=self.box).quantity, 3)
