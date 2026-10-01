import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Product
from apps.inventory.models import Stock
from apps.inventory.services import adjust_stock
from apps.sales.services import cancel_sale, create_sale, receive_sale


class RealizedProfitTests(TestCase):
    """Lucro previsto (`profit`) = todas as vendas confirmadas; lucro real (`realized_profit`) = só as
    já recebidas. Venda cancelada não conta em nenhum dos dois."""

    def setUp(self):
        self.user = get_user_model().objects.create_superuser("profit-admin", password="test-pass")
        self.product = Product.objects.create(sku="LUCRO", name="Controle")
        Stock.objects.get_or_create(product=self.product)
        adjust_stock(product_id=self.product.id, delta=20, reason="Inicial", actor=self.user, unit_cost=Decimal("10"))
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def sell(self, quantity, price="30", fee="0"):
        return create_sale(
            data=dict(
                idempotency_key=uuid.uuid4(),
                channel="direct",
                platform_fee=Decimal(fee),
                items=[dict(product_id=self.product.id, quantity=quantity, unit_price=Decimal(price))],
            ),
            actor=self.user,
        )

    def dashboard(self):
        body = self.client.get("/api/v1/dashboard/").json()
        return Decimal(body["profit"]), Decimal(body["realized_profit"])

    def test_without_sales_both_are_zero(self):
        self.assertEqual(self.dashboard(), (Decimal(0), Decimal(0)))

    def test_real_profit_counts_only_received_sales(self):
        received = self.sell(2)  # bruto 60, custo 20, lucro 40
        self.sell(1)  # bruto 30, custo 10, lucro 20, ainda a receber
        self.assertEqual(self.dashboard(), (Decimal("60.00"), Decimal(0)))
        receive_sale(sale_id=received.id, actor=self.user)
        self.assertEqual(self.dashboard(), (Decimal("60.00"), Decimal("40.00")))

    def test_real_profit_uses_the_real_fees_of_the_sale(self):
        sale = self.sell(1, price="30", fee="5")  # líquido 25, custo 10, lucro 15
        receive_sale(sale_id=sale.id, actor=self.user)
        self.assertEqual(self.dashboard(), (Decimal("15.00"), Decimal("15.00")))

    def test_cancelled_sale_counts_in_neither(self):
        sale = self.sell(2)
        receive_sale(sale_id=sale.id, actor=self.user)
        cancel_sale(sale_id=sale.id, actor=self.user)
        self.assertEqual(self.dashboard(), (Decimal(0), Decimal(0)))
