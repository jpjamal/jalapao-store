"""Regras de domínio puras: rodam sem banco (SimpleTestCase)."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from apps.catalog.domain.sku import sku, sku_initials
from apps.common.domain.money import money
from apps.inventory.domain.costing import check_value, outgoing_value
from apps.sales.domain.totals import sale_totals


class DinheiroTests(SimpleTestCase):
    def test_arredonda_meio_para_cima(self):
        self.assertEqual(money("2.345"), Decimal("2.35"))
        self.assertEqual(money(Decimal("2.344")), Decimal("2.34"))


class SkuTests(SimpleTestCase):
    def test_iniciais_sem_acento_e_sem_ligacao(self):
        self.assertEqual(sku_initials("Luminária de Pimentão 3D"), "LP3")
        self.assertEqual(sku_initials("de da do"), "PRD")
        self.assertEqual(sku("LP3", 7), "SKU-LP3-0007")


class CustoMedioTests(SimpleTestCase):
    def test_saida_parcial_pelo_custo_medio_e_total_leva_tudo(self):
        self.assertEqual(outgoing_value(available=3, value=Decimal("10.00"), quantity=1), Decimal("3.33"))
        self.assertEqual(outgoing_value(available=3, value=Decimal("10.00"), quantity=3), Decimal("10.00"))

    def test_sem_estoque_e_valor_fora_do_limite(self):
        with self.assertRaises(ValidationError):
            outgoing_value(available=1, value=Decimal("5"), quantity=2)
        with self.assertRaises(ValidationError):
            check_value(Decimal("-0.01"))


class TotaisDaVendaTests(SimpleTestCase):
    def test_bruto_e_liquido(self):
        t = sale_totals(items=[{"unit_price": Decimal("59.90"), "quantity": 2}],
                        discount=Decimal("0"), fee=Decimal("14.38"), shipping=Decimal("12.50"))
        self.assertEqual((t.gross, t.net), (Decimal("119.80"), Decimal("92.92")))

    def test_desconto_maior_que_bruto_recusa(self):
        with self.assertRaises(ValidationError):
            sale_totals(items=[{"unit_price": Decimal("10"), "quantity": 1}],
                        discount=Decimal("11"), fee=Decimal("0"), shipping=Decimal("0"))
