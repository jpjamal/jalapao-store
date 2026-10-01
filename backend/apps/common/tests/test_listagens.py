import uuid
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product
from apps.common.filters import fold_text
from apps.finance.models import CashCategory, CashEntry
from apps.inventory.models import Stock
from apps.inventory.services import adjust_stock, create_receipt
from apps.sales.services import create_sale, receive_sale
from apps.supplies.models import Supply, SupplyCategory
from apps.supplies.services import adjust_supply_stock, create_supply_receipt


class FoldTextTests(SimpleTestCase):
    def test_fold_removes_accents_and_case(self):
        self.assertEqual(fold_text("Água Ção ÇÃO Ñandú"), "agua cao cao nandu")
        self.assertEqual(fold_text(None), "")


class ListingTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("lists-admin", password="test-pass")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.category, _ = Category.objects.get_or_create(name="Eletrônicos")

    def names(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content)
        return [row.get("name") or row.get("description") or row.get("product_name") for row in response.json()["results"]]

    def product(self, name, price="10", stock=0, **extra):
        product = Product.objects.create(name=name, sale_price=Decimal(price), category=self.category, **extra)
        Stock.objects.get_or_create(product=product)
        if stock:
            adjust_stock(product_id=product.id, delta=stock, reason="Inicial", actor=self.user, unit_cost=Decimal("1"))
        return product


class ProductListTests(ListingTestCase):
    def setUp(self):
        super().setUp()
        for name in ["Zebra", "Água benta", "abajur", "Bola", "Árvore", "Álcool em gel"]:
            self.product(name)

    def test_search_ignores_accent_and_case(self):
        self.assertEqual(self.names("/api/v1/products/?search=agua"), ["Água benta"])
        self.assertEqual(self.names("/api/v1/products/?search=ALCOOL"), ["Álcool em gel"])
        self.assertEqual(self.names("/api/v1/products/?search=%C3%A1rvore"), ["Árvore"])
        self.assertEqual(self.names("/api/v1/products/?search=em+gel"), ["Álcool em gel"])

    def test_text_ordering_is_portuguese_not_byte_order(self):
        asc = self.names("/api/v1/products/?ordering=name")
        self.assertEqual(asc, ["abajur", "Água benta", "Álcool em gel", "Árvore", "Bola", "Zebra"])
        self.assertEqual(self.names("/api/v1/products/?ordering=-name"), list(reversed(asc)))

    def test_ordering_by_a_related_text_column_and_a_blank_one(self):
        other, _ = Category.objects.get_or_create(name="Água e sabão")
        Product.objects.filter(name="Bola").update(category=other)
        ordered = self.names("/api/v1/products/?ordering=category__name,name")
        self.assertEqual(ordered[0], "Bola")  # "Água e sabão" vem antes de "Eletrônicos"

    def test_unknown_ordering_field_is_ignored_without_error(self):
        default = self.names("/api/v1/products/")
        self.assertEqual(self.names("/api/v1/products/?ordering=password"), default)
        self.assertEqual(self.names("/api/v1/products/?ordering=stock__version"), default)


class ProductNumericAndFilterTests(ListingTestCase):
    def setUp(self):
        super().setUp()
        self.product("Barato", price="9", stock=5)
        self.product("Medio", price="10", stock=0)
        self.product("Caro", price="100", stock=2)
        self.product("Sem preco", price="0")

    def test_numbers_order_as_numbers(self):
        self.assertEqual(self.names("/api/v1/products/?ordering=sale_price"), ["Sem preco", "Barato", "Medio", "Caro"])
        self.assertEqual(self.names("/api/v1/products/?ordering=-sale_price"), ["Caro", "Medio", "Barato", "Sem preco"])

    def test_stock_quantity_ordering_and_in_stock_filter(self):
        self.assertEqual(self.names("/api/v1/products/?ordering=-stock__quantity")[:2], ["Barato", "Caro"])
        self.assertEqual(sorted(self.names("/api/v1/products/?in_stock=true")), ["Barato", "Caro"])
        self.assertEqual(sorted(self.names("/api/v1/products/?in_stock=false")), ["Medio", "Sem preco"])

    def test_filters_search_and_ordering_combine(self):
        url = "/api/v1/products/?in_stock=true&search=a&ordering=-sale_price"
        self.assertEqual(self.names(url), ["Caro", "Barato"])

    def test_ordering_is_stable_between_calls_when_values_tie(self):
        for i in range(6):
            self.product(f"Igual {i}", price="50")
        first = self.names("/api/v1/products/?ordering=sale_price")
        again = self.names("/api/v1/products/?ordering=sale_price")
        self.assertEqual(first, again)
        self.assertEqual(len(first), 10)

    def test_invalid_yes_no_filter_is_ignored(self):
        # filtro de sim/não com valor sem sentido não derruba a tela: vale como se não existisse
        everything = self.names("/api/v1/products/")
        self.assertEqual(self.names("/api/v1/products/?in_stock=talvez"), everything)


class StockHistoryListTests(ListingTestCase):
    def setUp(self):
        super().setUp()
        self.item = self.product("Controle", stock=10)
        adjust_stock(product_id=self.item.id, delta=-3, reason="Quebrou na entrega", actor=self.user)
        adjust_stock(product_id=self.item.id, delta=4, reason="Reposição da loja", actor=self.user, unit_cost=Decimal("2"))

    def reasons(self, url):
        return [m["reason"] for m in self.client.get(url).json()["results"]]

    def test_search_by_reason_product_and_sku(self):
        self.assertEqual(self.reasons("/api/v1/movements/?search=quebrou"), ["Quebrou na entrega"])
        self.assertEqual(len(self.reasons("/api/v1/movements/?search=controle")), 3)
        self.assertEqual(len(self.reasons(f"/api/v1/movements/?search={self.item.sku}")), 3)

    def test_direction_filter_and_ordering_by_delta(self):
        self.assertEqual(self.reasons("/api/v1/movements/?direction=out"), ["Quebrou na entrega"])
        self.assertEqual(len(self.reasons("/api/v1/movements/?direction=in")), 2)
        ordered = [m["delta"] for m in self.client.get("/api/v1/movements/?ordering=delta").json()["results"]]
        self.assertEqual(ordered, [-3, 4, 10])

    def test_period_filter_includes_the_whole_day(self):
        today = timezone.localdate()
        inside = f"/api/v1/movements/?date_from={today}&date_to={today}"
        self.assertEqual(len(self.reasons(inside)), 3)
        tomorrow = today + timedelta(days=1)
        self.assertEqual(self.reasons(f"/api/v1/movements/?date_from={tomorrow}"), [])
        yesterday = today - timedelta(days=1)
        self.assertEqual(self.reasons(f"/api/v1/movements/?date_to={yesterday}"), [])


class SalesAndReceiptsListTests(ListingTestCase):
    def setUp(self):
        super().setUp()
        self.item = self.product("Teclado especial", price="30", stock=20)
        self.sale = self.sell(2, reference="PEDIDO-ABC", channel="shopee")
        self.other = self.sell(1, reference="Balcão", channel="direct")
        receive_sale(sale_id=self.sale.id, actor=self.user)

    def sell(self, quantity, reference, channel):
        return create_sale(
            data=dict(
                idempotency_key=uuid.uuid4(), channel=channel, reference=reference,
                items=[dict(product_id=self.item.id, quantity=quantity, unit_price=Decimal("30"))],
            ),
            actor=self.user,
        )

    def refs(self, url):
        return [s["reference"] for s in self.client.get(url).json()["results"]]

    def test_sales_search_filters_and_ordering(self):
        self.assertEqual(self.refs("/api/v1/sales/?search=pedido"), ["PEDIDO-ABC"])
        self.assertEqual(len(self.refs("/api/v1/sales/?search=teclado")), 2)  # pelo produto dos itens, sem repetir
        self.assertEqual(self.refs("/api/v1/sales/?channel=direct"), ["Balcão"])
        self.assertEqual(self.refs("/api/v1/sales/?received=true"), ["PEDIDO-ABC"])
        self.assertEqual(self.refs("/api/v1/sales/?received=false"), ["Balcão"])
        self.assertEqual(self.refs("/api/v1/sales/?ordering=gross"), ["Balcão", "PEDIDO-ABC"])
        self.assertEqual(self.refs("/api/v1/sales/?ordering=-profit"), ["PEDIDO-ABC", "Balcão"])
        today = timezone.localdate()
        self.assertEqual(len(self.refs(f"/api/v1/sales/?date_from={today}&date_to={today}")), 2)

    def test_receipts_filters_by_payment_and_kind(self):
        def receipt(kind, name_ref):
            return create_receipt(
                data=dict(
                    idempotency_key=uuid.uuid4(), product_id=self.item.id, kind=kind, quantity=1,
                    unit_cost=Decimal("5"), occurred_on=timezone.localdate(), reference=name_ref, supplier="Fornecedor X",
                ),
                actor=self.user,
            )

        receipt("purchase", "Compra A")
        receipt("production", "Produção B")
        refs = lambda url: [r["reference"] for r in self.client.get(url).json()["results"]]  # noqa: E731
        self.assertEqual(refs("/api/v1/receipts/?kind=production"), ["Produção B"])
        self.assertEqual(refs("/api/v1/receipts/?paid=false"), ["Compra A"])  # produção nunca está "a pagar"
        self.assertEqual(refs("/api/v1/receipts/?paid=true"), [])
        self.assertEqual(sorted(refs("/api/v1/receipts/?search=fornecedor")), ["Compra A", "Produção B"])
        self.assertEqual(refs("/api/v1/receipts/?search=producao"), ["Produção B"])  # sem acento


class CashListTests(ListingTestCase):
    def setUp(self):
        super().setUp()
        self.taxes = CashCategory.objects.create(name="Água teste", direction="out")
        self.today = timezone.localdate()
        for description, amount, days in (("Conta de luz", "120", 0), ("Imposto MEI", "70", 10), ("Frete extra", "9", 20)):
            CashEntry.objects.create(
                direction="out", amount=Decimal(amount), description=description,
                occurred_on=self.today - timedelta(days=days), actor=self.user, category=self.taxes,
            )
        item = self.product("Item", price="30", stock=5)
        sale = create_sale(
            data=dict(idempotency_key=uuid.uuid4(), channel="direct",
                      items=[dict(product_id=item.id, quantity=1, unit_price=Decimal("30"))]),
            actor=self.user,
        )
        receive_sale(sale_id=sale.id, actor=self.user)

    def descriptions(self, url):
        return [e["description"] for e in self.client.get(url).json()["results"]]

    def test_search_by_description_and_category_name_without_accent(self):
        self.assertEqual(self.descriptions("/api/v1/cash/?search=luz"), ["Conta de luz"])
        self.assertEqual(len(self.descriptions("/api/v1/cash/?search=agua")), 3)  # pelo nome da categoria

    def test_origin_filter_and_amount_ordering(self):
        self.assertEqual(self.descriptions("/api/v1/cash/?origin=sale"), ["Recebimento de venda"])
        self.assertEqual(len(self.descriptions("/api/v1/cash/?origin=manual")), 3)
        amounts = [Decimal(e["amount"]) for e in self.client.get("/api/v1/cash/?ordering=amount").json()["results"]]
        self.assertEqual(amounts, [Decimal("9"), Decimal("30"), Decimal("70"), Decimal("120")])

    def test_period_filter(self):
        start = self.today - timedelta(days=12)
        end = self.today - timedelta(days=8)
        self.assertEqual(self.descriptions(f"/api/v1/cash/?date_from={start}&date_to={end}"), ["Imposto MEI"])

    def test_unknown_origin_is_a_400(self):
        self.assertEqual(self.client.get("/api/v1/cash/?origin=inventada").status_code, 400)


class SupplyListTests(ListingTestCase):
    def setUp(self):
        super().setUp()
        self.packs, _ = SupplyCategory.objects.get_or_create(name="Embalagens")
        self.box = Supply.objects.create(category=self.packs, name="Caixa média", unit="pacote")
        self.tape = Supply.objects.create(category=self.packs, name="Álcool isopropílico", unit="frasco")
        self.empty = Supply.objects.create(category=self.packs, name="Zip lock", unit="pacote")
        adjust_supply_stock(supply_id=self.box.id, delta=8, reason="Inicial", actor=self.user)
        adjust_supply_stock(supply_id=self.tape.id, delta=2, reason="Inicial", actor=self.user)

    def names_of(self, url):
        return [row["name"] for row in self.client.get(url).json()["results"]]

    def test_supplies_search_order_and_stock_filter(self):
        self.assertEqual(self.names_of("/api/v1/supplies/?search=alcool"), ["Álcool isopropílico"])
        self.assertEqual(self.names_of("/api/v1/supplies/?ordering=name"), ["Álcool isopropílico", "Caixa média", "Zip lock"])
        self.assertEqual(self.names_of("/api/v1/supplies/?ordering=-stock__quantity")[:2], ["Caixa média", "Álcool isopropílico"])
        self.assertEqual(self.names_of("/api/v1/supplies/?in_stock=false"), ["Zip lock"])
        self.assertEqual(sorted(self.names_of("/api/v1/supplies/?in_stock=true")), ["Caixa média", "Álcool isopropílico"])

    def test_supply_receipts_and_movements(self):
        create_supply_receipt(
            data=dict(idempotency_key=uuid.uuid4(), supply_id=self.box.id, quantity=3, unit_cost=Decimal("4"),
                      occurred_on=timezone.localdate(), supplier="Casa das Embalagens", reference="NF 77"),
            actor=self.user,
        )
        receipts = lambda url: [r["reference"] for r in self.client.get(url).json()["results"]]  # noqa: E731
        self.assertEqual(receipts("/api/v1/supply-receipts/?search=embalagens"), ["NF 77"])
        self.assertEqual(receipts("/api/v1/supply-receipts/?paid=false"), ["NF 77"])
        self.assertEqual(receipts("/api/v1/supply-receipts/?paid=true"), [])
        deltas = [m["delta"] for m in self.client.get("/api/v1/supply-movements/?direction=in&ordering=-delta").json()["results"]]
        self.assertEqual(deltas, [8, 3, 2])
        found = [m["reason"] for m in self.client.get("/api/v1/supply-movements/?search=caixa").json()["results"]]
        self.assertEqual(len(found), 2)
