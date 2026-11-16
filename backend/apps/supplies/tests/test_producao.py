"""Spec 041 — componentes da peça 3D, filamento em gramas e baixa dos insumos na produção."""

import uuid
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import SimpleTestCase, TestCase, TransactionTestCase
from rest_framework.test import APIClient

from apps.catalog.domain.pricing import printing_cost
from apps.catalog.models import Product
from apps.inventory.models import Receipt
from apps.inventory.services import cancel_receipt, create_receipt
from apps.supplies.models import ProductionSupply, Supply, SupplyCategory, SupplyMovement, SupplyStock
from apps.supplies.services import (
    cancel_supply_receipt,
    create_supply_receipt,
    register_supply_adjustment,
)

# peça de 2 h, 200 W, R$ 1,56 o kWh, sem mão de obra nem custo fixo, margem de 100%
BASE = dict(power_w="200", hours=2, minutes=0, energy_price_kwh="1.56", labor_cost="0", fixed_cost="0", markup_percent="100")


class ComponentCostTests(SimpleTestCase):
    def test_componentes_entram_no_custo_antes_da_margem(self):
        cost, price = printing_cost(
            filament_price_kg="1", weight_g="1", **BASE,
            filament_lines=[("120", "100", "1000")],
            component_lines=[(2, "3.50"), (4, "0.10")],
        )
        # 12,00 de filamento + 7,40 de componentes + 0,624 de energia = 20,024 -> 20,02; margem 100% -> 40,05
        self.assertEqual((cost, price), (Decimal("20.02"), Decimal("40.05")))

    def test_sem_componentes_a_conta_nao_muda(self):
        self.assertEqual(
            printing_cost(filament_price_kg="115", weight_g="45", **BASE),
            printing_cost(filament_price_kg="115", weight_g="45", **BASE, component_lines=[]),
        )


class ProducaoTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("producao-3d", password="test-pass")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.fil_cat, _ = SupplyCategory.objects.get_or_create(name="Filamentos", defaults={"is_filament": True})
        self.parts = SupplyCategory.objects.get(name="Componentes")
        self.pla = Supply.objects.create(
            category=self.fil_cat, name="PLA Preto", material="PLA", color="Preto", unit="g",
            roll_weight_g=Decimal("1000"), roll_price=Decimal("100.00"),
        )
        self.led = Supply.objects.create(category=self.parts, name="LED 001")
        self.screw = Supply.objects.create(category=self.parts, name="Parafuso M3")
        self.buy(self.pla, 1, "100.00")
        self.buy(self.led, 10, "3.50")
        register_supply_adjustment(
            supply_id=self.screw.id, delta=50, reason="Já tinha em casa", actor=self.user, unit_cost=Decimal("0.10")
        )

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

    def create_lamp(self, grams="120", leds=2, screws=4):
        response = self.client.post(
            "/api/v1/products/",
            {
                "name": "Luminária Air Form",
                "printing": {
                    **BASE,
                    "filaments": [{"filament": str(self.pla.id), "grams": grams}],
                    "components": [
                        {"supply": str(self.led.id), "quantity": leds},
                        {"supply": str(self.screw.id), "quantity": screws},
                    ],
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()

    def produce(self, product_id, quantity, consume=True, kind="production"):
        return create_receipt(
            data=dict(
                idempotency_key=uuid.uuid4(), product_id=product_id, kind=kind, quantity=quantity,
                unit_cost=Decimal("20.02"), occurred_on=date(2026, 11, 16), consume_supplies=consume,
            ),
            actor=self.user,
        )

    # --- filamento em gramas ---
    def test_compra_de_filamento_entra_em_gramas(self):
        self.assertEqual(self.stock(self.pla).quantity, 1000)
        self.buy(self.pla, 2, "95.00")
        self.assertEqual(self.stock(self.pla).quantity, 3000)

    def test_cancelar_compra_de_filamento_tira_as_gramas(self):
        receipt = self.buy(self.pla, 2, "95.00")
        cancel_supply_receipt(receipt_id=receipt.id, actor=self.user)
        self.assertEqual(self.stock(self.pla).quantity, 1000)

    def test_ajuste_de_filamento_e_em_gramas_e_sem_custo(self):
        register_supply_adjustment(supply_id=self.pla.id, delta=-250, reason="Pesei o rolo", actor=self.user)
        self.assertEqual(self.stock(self.pla).quantity, 750)
        with self.assertRaises(ValidationError):
            register_supply_adjustment(
                supply_id=self.pla.id, delta=100, reason="Sobra", actor=self.user, unit_cost=Decimal("0.10")
            )

    def test_cadastro_de_filamento_fica_com_unidade_em_gramas(self):
        response = self.client.post(
            "/api/v1/supplies/",
            {
                "category": str(self.fil_cat.id), "name": "PETG Branco", "unit": "rolo", "material": "PETG",
                "color": "Branco", "roll_weight_g": "1000", "roll_price": "110.00",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["unit"], "g")

    # --- componentes no custo da peça ---
    def test_componentes_entram_no_custo_da_peca(self):
        body = self.create_lamp()
        self.assertEqual((body["cost_price"], body["sale_price"]), ("20.02", "40.05"))
        lines = {line["supply_name"]: line for line in body["printing"]["components"]}
        self.assertEqual((lines["LED 001"]["quantity"], lines["LED 001"]["unit_cost"]), (2, "3.50"))
        self.assertFalse(lines["LED 001"]["price_outdated"])

    def test_filamento_nao_entra_como_componente(self):
        response = self.client.post(
            "/api/v1/products/",
            {"name": "Peça", "printing": {**BASE, "weight_g": "10", "components": [{"supply": str(self.pla.id), "quantity": 1}]}},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_componente_repetido_e_recusado(self):
        line = {"supply": str(self.led.id), "quantity": 1}
        response = self.client.post(
            "/api/v1/products/",
            {"name": "Peça", "printing": {**BASE, "weight_g": "10", "components": [line, line]}},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_custo_do_componente_fica_congelado_ate_o_dono_pedir(self):
        body = self.create_lamp()
        self.buy(self.led, 10, "4.00")
        url = f"/api/v1/products/{body['id']}/"
        again = self.client.get(url).json()
        led = next(line for line in again["printing"]["components"] if line["supply_name"] == "LED 001")
        self.assertEqual((led["unit_cost"], led["price_outdated"]), ("3.50", True))
        self.assertEqual(again["cost_price"], "20.02")
        updated = self.client.patch(
            url,
            {"printing": {"components": [
                {"supply": str(self.led.id), "quantity": 2, "refresh_price": True},
                {"supply": str(self.screw.id), "quantity": 4},
            ]}},
            format="json",
        ).json()
        # LED a 4,00: + 1,00 no custo
        self.assertEqual(updated["cost_price"], "21.02")

    # --- produção ---
    def test_producao_baixa_filamento_e_componentes(self):
        lamp = self.create_lamp()
        receipt = self.produce(lamp["id"], 3)
        self.assertEqual(self.stock(self.pla).quantity, 1000 - 360)
        self.assertEqual(self.stock(self.led).quantity, 10 - 6)
        self.assertEqual(self.stock(self.screw).quantity, 50 - 12)
        lines = {line.supply_name: (line.requested, line.taken) for line in receipt.supply_lines.all()}
        self.assertEqual(lines, {"PLA Preto": (360, 360), "LED 001": (6, 6), "Parafuso M3": (12, 12)})
        movement = SupplyMovement.objects.get(supply=self.led, production=receipt)
        self.assertEqual(movement.delta, -6)
        self.assertIn("Produção", movement.reason)

    def test_gramas_fracionadas_arredondam_para_cima(self):
        lamp = self.create_lamp(grams="12.5")
        self.produce(lamp["id"], 3)
        self.assertEqual(self.stock(self.pla).quantity, 1000 - 38)

    def test_falta_de_saldo_nao_impede_a_producao(self):
        lamp = self.create_lamp(leds=4)
        receipt = self.produce(lamp["id"], 3)
        line = receipt.supply_lines.get(supply=self.led)
        self.assertEqual((line.requested, line.taken), (12, 10))
        self.assertEqual(self.stock(self.led).quantity, 0)
        self.assertEqual(Product.objects.get(pk=lamp["id"]).stock.quantity, 3)

    def test_producao_sem_baixa_nao_mexe_nos_insumos(self):
        lamp = self.create_lamp()
        receipt = self.produce(lamp["id"], 3, consume=False)
        self.assertEqual(self.stock(self.led).quantity, 10)
        self.assertFalse(receipt.supply_lines.exists())

    def test_compra_de_produto_nao_baixa_insumos(self):
        lamp = self.create_lamp()
        self.produce(lamp["id"], 2, kind="purchase")
        self.assertEqual(self.stock(self.led).quantity, 10)

    def test_cancelar_producao_devolve_os_insumos(self):
        lamp = self.create_lamp()
        register_supply_adjustment(supply_id=self.led.id, delta=2, reason="Achei mais", actor=self.user)
        self.assertEqual((self.stock(self.led).quantity, self.stock(self.led).uncosted), (12, 2))
        receipt = self.produce(lamp["id"], 2)
        self.assertEqual((self.stock(self.led).quantity, self.stock(self.led).uncosted), (8, 0))
        cancel_receipt(receipt_id=receipt.id, actor=self.user)
        self.assertEqual((self.stock(self.led).quantity, self.stock(self.led).uncosted), (12, 2))
        self.assertEqual(self.stock(self.pla).quantity, 1000)
        self.assertEqual(Receipt.objects.get(pk=receipt.id).status, Receipt.Status.CANCELLED)

    def test_produto_sem_parametros_3d_nao_baixa_nada(self):
        product = Product.objects.create(name="Revenda")
        receipt = self.produce(product.id, 2)
        self.assertFalse(ProductionSupply.objects.filter(production=receipt).exists())

    def test_api_da_producao_mostra_o_que_saiu(self):
        lamp = self.create_lamp()
        response = self.client.post(
            "/api/v1/receipts/",
            {
                "idempotency_key": str(uuid.uuid4()), "product_id": lamp["id"], "kind": "production",
                "quantity": 1, "unit_cost": "20.02", "occurred_on": "2026-11-16",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        lines = {line["supply_name"]: (line["requested"], line["taken"], line["unit"]) for line in response.json()["supply_lines"]}
        self.assertEqual(lines["PLA Preto"], (120, 120, "g"))
        self.assertEqual(lines["LED 001"], (2, 2, "unidade"))


class FilamentoEmGramasMigrationTests(TransactionTestCase):
    def test_saldo_e_historico_em_rolos_viram_gramas(self):
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        before = [("supplies", "0008_componentes_e_producao")]
        executor.migrate(before)
        try:
            old = executor.loader.project_state(before).apps
            Category = old.get_model("supplies", "SupplyCategory")
            OldSupply = old.get_model("supplies", "Supply")
            Stock = old.get_model("supplies", "SupplyStock")
            Movement = old.get_model("supplies", "SupplyMovement")
            User = old.get_model("accounts", "User")
            user = User.objects.create(username="migra-gramas")
            cat = Category.objects.filter(is_filament=True).first() or Category.objects.create(
                name="Filamentos", is_filament=True, counts_as_expense=False
            )
            supply = OldSupply.objects.create(
                category=cat, name="PLA Migrado", unit="rolo", material="PLA", color="Azul",
                roll_weight_g=Decimal("750"), roll_price=Decimal("80"),
            )
            Stock.objects.create(supply=supply, quantity=3, uncosted=3)
            Movement.objects.create(supply=supply, delta=3, balance_after=3, reason="Inicial", actor=user)
            supply_id = supply.id
        finally:
            MigrationExecutor(connection).migrate(latest)
        supply = Supply.objects.get(pk=supply_id)
        stock = SupplyStock.objects.get(supply=supply)
        self.assertEqual((supply.unit, stock.quantity, stock.uncosted), ("g", 2250, 2250))
        movement = SupplyMovement.objects.get(supply=supply)
        self.assertEqual((movement.delta, movement.balance_after), (2250, 2250))
        self.assertFalse(SupplyCategory.objects.get(name="Componentes").counts_as_expense)
