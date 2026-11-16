"""Spec 040 — custo dos insumos (embalagens) no lucro da venda, sem contar duas vezes."""

import uuid
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Product
from apps.finance.services import supply_expense
from apps.inventory.models import Stock
from apps.inventory.services import adjust_stock
from apps.sales.services import cancel_sale, create_sale, edit_sale
from apps.supplies.models import ProductSupply, Supply, SupplyCategory, SupplyStock
from apps.supplies.services import (
    adjust_supply_stock,
    cancel_supply_receipt,
    create_supply_receipt,
    pay_supply_receipt,
    register_supply_adjustment,
)


class CustoNaVendaTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("custo-insumo")
        self.packaging = SupplyCategory.objects.get(name="Embalagens")
        self.labels, _ = SupplyCategory.objects.get_or_create(name="Etiquetas e papelaria")
        self.box = Supply.objects.create(category=self.packaging, name="Caixa M")
        self.bag = Supply.objects.create(category=self.packaging, name="Saco 20x30")
        self.product = Product.objects.create(sku="CUSTO-INS", name="Caneca")
        Stock.objects.get_or_create(product=self.product)
        adjust_stock(product_id=self.product.id, delta=20, reason="Inicial", actor=self.user, unit_cost=Decimal("5"))

    def buy(self, supply, quantity, unit_cost):
        return create_supply_receipt(
            data=dict(
                idempotency_key=uuid.uuid4(), supply_id=supply.id, quantity=quantity,
                unit_cost=Decimal(unit_cost), occurred_on=date(2026, 11, 1),
            ),
            actor=self.user,
        )

    def stock(self, supply):
        return SupplyStock.objects.get(supply=supply)

    def sell(self, supplies, quantity=1):
        return create_sale(
            data=dict(
                idempotency_key=uuid.uuid4(),
                channel="direct",
                items=[dict(product_id=self.product.id, quantity=quantity, unit_price=Decimal("30"))],
                supplies=supplies,
            ),
            actor=self.user,
        )

    # --- regra da categoria ---
    def test_embalagens_deixa_de_contar_como_despesa_na_compra(self):
        self.assertFalse(self.packaging.counts_as_expense)

    # --- custo na venda ---
    def test_embalagem_comprada_desconta_do_lucro_da_venda(self):
        self.buy(self.box, 10, "2.00")
        self.buy(self.bag, 10, "0.30")
        sale = self.sell([{"supply_id": self.box.id, "quantity": 1}, {"supply_id": self.bag.id, "quantity": 2}])
        self.assertEqual(sale.supplies_cost, Decimal("2.60"))
        # 30 de venda − 5 do produto − 2,60 de embalagem
        self.assertEqual(sale.profit, Decimal("22.40"))
        linha = sale.supply_lines.get(supply=self.bag)
        self.assertEqual((linha.unit_cost, linha.zero_cost_qty, linha.cost_total), (Decimal("0.30"), 0, Decimal("0.60")))

    def test_compra_que_conta_como_despesa_sai_sem_custo_na_venda(self):
        label = Supply.objects.create(category=self.labels, name="Etiqueta térmica")
        self.assertTrue(self.labels.counts_as_expense)
        self.buy(label, 100, "0.10")
        sale = self.sell([{"supply_id": label.id, "quantity": 1}])
        self.assertEqual((sale.supplies_cost, sale.profit), (Decimal("0"), Decimal("25.00")))

    def test_saldo_antigo_sai_primeiro_e_sem_custo(self):
        adjust_supply_stock(supply_id=self.box.id, delta=2, reason="Saldo de antes", actor=self.user)
        self.buy(self.box, 5, "1.50")
        self.assertEqual((self.stock(self.box).quantity, self.stock(self.box).uncosted), (7, 2))
        sale = self.sell([{"supply_id": self.box.id, "quantity": 3}])
        linha = sale.supply_lines.get()
        self.assertEqual((linha.taken, linha.zero_cost_qty, linha.cost_total), (3, 2, Decimal("1.50")))
        self.assertEqual((self.stock(self.box).quantity, self.stock(self.box).uncosted), (4, 0))

    def test_baixa_manual_consome_a_parte_sem_custo_primeiro(self):
        adjust_supply_stock(supply_id=self.box.id, delta=2, reason="Saldo de antes", actor=self.user)
        self.buy(self.box, 5, "1.50")
        register_supply_adjustment(supply_id=self.box.id, delta=-3, reason="Rasgou", actor=self.user)
        self.assertEqual((self.stock(self.box).quantity, self.stock(self.box).uncosted), (4, 0))

    def test_filamento_nao_sai_na_venda(self):
        # spec 041: filamento é contado em gramas e sai na produção da peça, não na venda
        filaments = SupplyCategory.objects.get(is_filament=True, name="Filamentos")
        pla = Supply.objects.create(
            category=filaments, name="PLA preto", material="PLA", color="Preto",
            roll_weight_g=Decimal("1000"), roll_price=Decimal("100"),
        )
        self.buy(pla, 2, "100.00")
        with self.assertRaises(ValidationError):
            self.sell([{"supply_id": pla.id, "quantity": 1}])
        self.assertEqual(self.stock(pla).quantity, 2000)

    def test_cancelar_a_venda_devolve_cada_parte_ao_seu_lugar(self):
        adjust_supply_stock(supply_id=self.box.id, delta=1, reason="Saldo de antes", actor=self.user)
        self.buy(self.box, 4, "2.00")
        sale = self.sell([{"supply_id": self.box.id, "quantity": 3}])
        self.assertEqual((self.stock(self.box).quantity, self.stock(self.box).uncosted), (2, 0))
        cancel_sale(sale_id=sale.id, actor=self.user)
        self.assertEqual((self.stock(self.box).quantity, self.stock(self.box).uncosted), (5, 1))

    def test_editar_a_venda_mantem_o_custo_da_embalagem_no_lucro(self):
        self.buy(self.box, 10, "2.00")
        sale = self.sell([{"supply_id": self.box.id, "quantity": 1}])
        sale = edit_sale(
            sale_id=sale.id,
            data={"request_key": uuid.uuid4(), "expected_updated_at": sale.updated_at, "discount": Decimal("3")},
            actor=self.user,
        )
        self.assertEqual(sale.profit, Decimal("20.00"))  # 30 − 3 − 5 − 2

    # --- custo unitário ---
    def test_compra_define_o_custo_e_cancelar_volta_ao_anterior(self):
        self.buy(self.box, 10, "2.00")
        receipt = self.buy(self.box, 10, "2.50")
        self.box.refresh_from_db()
        self.assertEqual(self.box.unit_cost, Decimal("2.50"))
        cancel_supply_receipt(receipt_id=receipt.id, actor=self.user)
        self.box.refresh_from_db()
        self.assertEqual(self.box.unit_cost, Decimal("2.00"))
        self.assertEqual((self.stock(self.box).quantity, self.stock(self.box).uncosted), (10, 0))

    def test_ajuste_de_entrada_com_custo_entra_com_custo_e_nao_mexe_no_caixa(self):
        register_supply_adjustment(
            supply_id=self.bag.id, delta=80, reason="Sacos que já tinha", actor=self.user, unit_cost=Decimal("0.25")
        )
        self.bag.refresh_from_db()
        self.assertEqual(self.bag.unit_cost, Decimal("0.25"))
        self.assertEqual((self.stock(self.bag).quantity, self.stock(self.bag).uncosted), (80, 0))
        sale = self.sell([{"supply_id": self.bag.id, "quantity": 2}])
        self.assertEqual(sale.supplies_cost, Decimal("0.50"))
        self.assertEqual(supply_expense(), Decimal("0"))

    def test_ajuste_sem_custo_entra_sem_custo(self):
        register_supply_adjustment(supply_id=self.bag.id, delta=5, reason="Contagem", actor=self.user)
        self.assertEqual(self.stock(self.bag).uncosted, 5)

    def test_custo_so_vale_em_ajuste_de_entrada(self):
        register_supply_adjustment(supply_id=self.bag.id, delta=5, reason="Contagem", actor=self.user)
        with self.assertRaises(ValidationError):
            register_supply_adjustment(
                supply_id=self.bag.id, delta=-1, reason="Perda", actor=self.user, unit_cost=Decimal("1")
            )

    # --- resultado do negócio: o custo da embalagem conta uma vez só ---
    def test_compra_de_embalagem_paga_nao_e_despesa_e_o_custo_vem_pela_venda(self):
        receipt = self.buy(self.box, 10, "2.00")
        pay_supply_receipt(receipt_id=receipt.id, occurred_on=date(2026, 11, 2), actor=self.user)
        self.assertEqual(supply_expense(), Decimal("0"))
        sale = self.sell([{"supply_id": self.box.id, "quantity": 1}])
        self.assertEqual(sale.supplies_cost, Decimal("2.00"))


class ApiCustoNaVendaTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("api-custo-insumo")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        packaging = SupplyCategory.objects.get(name="Embalagens")
        self.box = Supply.objects.create(category=packaging, name="Caixa M")
        self.bag = Supply.objects.create(category=packaging, name="Saco 20x30")
        self.product = Product.objects.create(sku="KIT-1", name="Caneca", cost_price=Decimal("5"), sale_price=Decimal("30"))
        Stock.objects.get_or_create(product=self.product)
        adjust_stock(product_id=self.product.id, delta=5, reason="Inicial", actor=self.user, unit_cost=Decimal("5"))

    def test_ajuste_com_custo_pela_api_e_saldo_sem_custo_na_leitura(self):
        resposta = self.client.post(
            "/api/v1/supply-movements/",
            {"supply": str(self.bag.id), "delta": 10, "reason": "Já tinha", "unit_cost": "0.25"},
            format="json",
        )
        self.assertEqual(resposta.status_code, 201, resposta.json())
        self.client.post(
            "/api/v1/supply-movements/", {"supply": str(self.bag.id), "delta": 2, "reason": "Contagem"}, format="json"
        )
        lido = self.client.get(f"/api/v1/supplies/{self.bag.id}/").json()
        self.assertEqual((lido["unit_cost"], lido["quantity"], lido["uncosted"]), ("0.25", 12, 2))

    def test_custo_unitario_nao_se_edita_a_mao(self):
        self.client.patch(f"/api/v1/supplies/{self.box.id}/", {"unit_cost": "9.99"}, format="json")
        self.box.refresh_from_db()
        self.assertIsNone(self.box.unit_cost)

    def test_embalagem_padrao_do_produto(self):
        resposta = self.client.patch(
            f"/api/v1/products/{self.product.id}/",
            {"default_supplies": [{"supply": str(self.box.id), "quantity": 1}, {"supply": str(self.bag.id), "quantity": 2}]},
            format="json",
        )
        self.assertEqual(resposta.status_code, 200, resposta.json())
        kit = {row["supply_name"]: row["quantity"] for row in resposta.json()["default_supplies"]}
        self.assertEqual(kit, {"Caixa M": 1, "Saco 20x30": 2})
        # trocar a lista substitui; lista vazia limpa
        self.client.patch(
            f"/api/v1/products/{self.product.id}/",
            {"default_supplies": [{"supply": str(self.bag.id), "quantity": 1}]},
            format="json",
        )
        self.assertEqual(list(ProductSupply.objects.values_list("supply__name", "quantity")), [("Saco 20x30", 1)])
        self.client.patch(f"/api/v1/products/{self.product.id}/", {"default_supplies": []}, format="json")
        self.assertFalse(ProductSupply.objects.exists())

    def test_embalagem_padrao_recusa_filamento_e_repetido(self):
        filaments = SupplyCategory.objects.get(is_filament=True, name="Filamentos")
        pla = Supply.objects.create(category=filaments, name="PLA", material="PLA", color="Preto")
        resposta = self.client.patch(
            f"/api/v1/products/{self.product.id}/",
            {"default_supplies": [{"supply": str(pla.id), "quantity": 1}]},
            format="json",
        )
        self.assertEqual(resposta.status_code, 400)
        repetido = self.client.patch(
            f"/api/v1/products/{self.product.id}/",
            {"default_supplies": [{"supply": str(self.box.id), "quantity": 1}, {"supply": str(self.box.id), "quantity": 2}]},
            format="json",
        )
        self.assertEqual(repetido.status_code, 400)

    def test_venda_mostra_o_custo_dos_insumos(self):
        self.client.post(
            "/api/v1/supply-movements/",
            {"supply": str(self.box.id), "delta": 5, "reason": "Já tinha", "unit_cost": "2.00"},
            format="json",
        )
        resposta = self.client.post(
            "/api/v1/sales/",
            {
                "idempotency_key": str(uuid.uuid4()),
                "channel": "direct",
                "items": [{"product_id": str(self.product.id), "quantity": 1, "unit_price": "30"}],
                "supplies": [{"supply_id": str(self.box.id), "quantity": 1}],
            },
            format="json",
        )
        self.assertEqual(resposta.status_code, 201, resposta.json())
        venda = resposta.json()
        self.assertEqual(venda["supplies_cost"], "2.00")
        self.assertEqual(venda["supplies"][0]["cost_total"], "2.00")
