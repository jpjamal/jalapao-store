"""Spec 015 — vendas do Mercado Livre importadas sob comando do dono. Sem rede."""

import copy
from contextlib import contextmanager
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.catalog.models import Product
from apps.integrations import base
from apps.integrations.base import IntegrationError
from apps.integrations.meli import pedidos
from apps.integrations.models import Listing, MarketplaceAccount
from apps.inventory.services import adjust_stock
from apps.sales.models import Sale

# formato da documentação "Orders": order_items com sale_fee, payments com marketplace_fee
PEDIDO = {
    "id": 2000001,
    "status": "paid",
    "date_created": "2026-09-20T10:00:00.000-03:00",
    "order_items": [{"item": {"id": "MLB7700023302", "title": "Dummy Aranha"}, "quantity": 2,
                     "unit_price": 59.9, "sale_fee": 7.19}],
    "payments": [{"id": 1, "transaction_amount": 119.8, "marketplace_fee": 14.38}],
    "shipping": {"id": 44001},
}


class Pedidos:
    """Mercado Livre de mentira: `pedidos` é o que a conta tem, por id."""

    channel = "mercado_livre"
    pedidos = {}
    frete = {"senders": [{"user_id": 96417426, "cost": 12.5}]}
    chamadas = []

    def orders_search(self, *, account, status, date_from, offset=0, limit=50):
        Pedidos.chamadas.append(("orders_search", status))
        resultados = [p for p in Pedidos.pedidos.values() if p["status"] == status]
        return {"results": resultados[offset:offset + limit], "paging": {"total": len(resultados)}}

    def order(self, *, account, order_id):
        Pedidos.chamadas.append(("order", order_id))
        return copy.deepcopy(Pedidos.pedidos[int(order_id)])

    def shipment_costs(self, *, account, shipment_id):
        Pedidos.chamadas.append(("shipment_costs", shipment_id))
        if Pedidos.frete is None:
            raise IntegrationError("O Mercado Livre não liberou esta consulta para a sua conta (HTTP 403).")
        return Pedidos.frete


@contextmanager
def mercado_livre(*lista, frete="padrao"):
    original = base._ADAPTADORES.get("mercado_livre")
    Pedidos.pedidos = {p["id"]: copy.deepcopy(p) for p in lista}
    Pedidos.frete = {"senders": [{"user_id": 96417426, "cost": 12.5}]} if frete == "padrao" else frete
    Pedidos.chamadas = []
    base._ADAPTADORES["mercado_livre"] = Pedidos
    try:
        yield Pedidos
    finally:
        base._ADAPTADORES["mercado_livre"] = original


class Base(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("dono")
        MarketplaceAccount.objects.create(
            channel="mercado_livre", external_id="96417426", active=True,
            access_token="tok", refresh_token="ref",
            token_expires_at=timezone.now() + timedelta(hours=5),
        )
        self.produto = Product.objects.create(name="Dummy Aranha", cost_price=Decimal("7.36"))
        adjust_stock(product_id=self.produto.id, delta=5, reason="Produção 3D", actor=self.user, unit_cost=Decimal("7.36"))
        Listing.objects.create(product=self.produto, marketplace="mercado_livre",
                               seller_id="96417426", item_id="MLB7700023302")

    def estoque(self):
        self.produto.stock.refresh_from_db()
        return self.produto.stock.quantity


class PreviaTests(Base):
    def test_pedido_novo_com_taxa_e_frete_reais(self):
        with mercado_livre(PEDIDO):
            linhas = pedidos.previa()
        p = linhas[0]
        self.assertEqual((p["order_id"], p["situacao"]), ("2000001", "nova"))
        self.assertEqual(p["bruto"], Decimal("119.80"))
        self.assertEqual(p["taxa"], Decimal("14.38"))  # marketplace_fee do pagamento
        self.assertEqual(p["frete"], Decimal("12.50"))
        self.assertEqual(p["liquido"], Decimal("92.92"))
        self.assertEqual(Sale.objects.count(), 0)  # prévia não cria nada

    def test_taxa_cai_para_sale_fee_vezes_quantidade(self):
        sem_taxa_no_pagamento = {**PEDIDO, "payments": [{"id": 1}]}
        self.assertEqual(pedidos.taxa_do_pedido(sem_taxa_no_pagamento), Decimal("14.38"))

    def test_anuncio_sem_vinculo_fica_pendente(self):
        outro = {**PEDIDO, "id": 2000002, "order_items": [{**PEDIDO["order_items"][0], "item": {"id": "MLB999"}}]}
        with mercado_livre(outro):
            p = pedidos.previa()[0]
        self.assertEqual(p["situacao"], "pendente")
        self.assertIn("sem produto vinculado", p["problemas"][0])

    def test_frete_nao_lido_vira_aviso(self):
        with mercado_livre(PEDIDO, frete=None):
            p = pedidos.previa()[0]
        self.assertIsNone(p["frete"])
        self.assertIn("frete zero", p["avisos"][0])
        self.assertEqual(p["situacao"], "nova")


class ImportacaoTests(Base):
    def test_importa_baixa_estoque_e_fica_a_receber(self):
        with mercado_livre(PEDIDO):
            r = pedidos.importar(["2000001"], actor=self.user)
        self.assertEqual(r["importadas"], ["2000001"])
        venda = Sale.objects.get()
        self.assertEqual((venda.channel, venda.external_id), ("mercado_livre", "2000001"))
        self.assertEqual(venda.reference, "Pedido ML 2000001")
        self.assertEqual((venda.gross, venda.platform_fee, venda.shipping_cost, venda.net),
                         (Decimal("119.80"), Decimal("14.38"), Decimal("12.50"), Decimal("92.92")))
        self.assertIsNone(venda.received_at)  # caixa só quando o dono marcar recebida
        self.assertEqual(self.estoque(), 3)

    def test_mesmo_pedido_nunca_vira_duas_vendas(self):
        with mercado_livre(PEDIDO):
            pedidos.importar(["2000001"], actor=self.user)
            r = pedidos.importar(["2000001", "2000001"], actor=self.user)
            self.assertEqual(pedidos.previa()[0]["situacao"], "importada")
        self.assertEqual(r["ignoradas"], [{"order_id": "2000001", "motivo": "já importado"}])
        self.assertEqual(Sale.objects.count(), 1)
        self.assertEqual(self.estoque(), 3)

    def test_pedido_cancelado_cancela_a_venda_e_devolve_estoque(self):
        with mercado_livre(PEDIDO):
            pedidos.importar(["2000001"], actor=self.user)
        cancelado = {**PEDIDO, "status": "cancelled"}
        with mercado_livre(cancelado):
            self.assertEqual(pedidos.previa()[0]["situacao"], "cancelar")
            r = pedidos.importar(["2000001"], actor=self.user)
        self.assertEqual(r["canceladas"], ["2000001"])
        self.assertEqual(Sale.objects.get().status, "cancelled")
        self.assertEqual(self.estoque(), 5)

    def test_sem_estoque_falha_sem_criar_venda(self):
        muitos = {**PEDIDO, "order_items": [{**PEDIDO["order_items"][0], "quantity": 9}]}
        with mercado_livre(muitos):
            r = pedidos.importar(["2000001"], actor=self.user)
        self.assertEqual(r["falhas"][0]["order_id"], "2000001")
        self.assertEqual(Sale.objects.count(), 0)
        self.assertEqual(self.estoque(), 5)

    def test_numeros_vem_do_mercado_livre_nao_da_tela(self):
        with mercado_livre(PEDIDO) as ml:
            pedidos.importar(["2000001"], actor=self.user)
        self.assertIn(("order", "2000001"), ml.chamadas)


class ApiTests(Base):
    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def test_exige_permissao(self):
        comum = get_user_model().objects.create_user("vendedor")
        comum.user_permissions.set(Permission.objects.filter(codename__in=["view_sale", "add_sale"]))
        self.client.force_authenticate(get_user_model().objects.get(pk=comum.pk))
        with mercado_livre(PEDIDO) as ml:
            self.assertEqual(self.client.get("/api/v1/sales/ml-preview/").status_code, 403)
        self.assertEqual(ml.chamadas, [])

    def test_previa_e_importacao_pela_api(self):
        self.client.force_authenticate(self.user)
        with mercado_livre(PEDIDO):
            r = self.client.get("/api/v1/sales/ml-preview/?days=7")
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json()["pedidos"][0]["situacao"], "nova")
            self.assertEqual(self.client.post("/api/v1/sales/ml-import/", {"order_ids": ["abc"]},
                                              format="json").status_code, 400)
            r = self.client.post("/api/v1/sales/ml-import/", {"order_ids": ["2000001"]}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()["importadas"], ["2000001"])

    def test_canal_site_jalapao_na_venda_manual(self):
        self.assertIn(("site", "Site Jalapão"), Sale.Channel.choices)


class ClientePedidosTests(Base):
    def test_caminhos_da_documentacao(self):
        from apps.integrations.meli.cliente import HttpResponse, MercadoLivreAdapter

        pedidos_http = []

        def transporte(method, path, **kwargs):
            pedidos_http.append(path)
            return HttpResponse(200, {"results": [], "paging": {"total": 0}, "senders": []}, {})

        adap = MercadoLivreAdapter(transporte=transporte, config={
            "client_id": "1", "client_secret": "s", "redirect_uri": "https://x/cb",
        })
        conta = MarketplaceAccount.objects.get()
        adap.orders_search(account=conta, status="paid", date_from="2026-09-01T00:00:00.000-03:00")
        adap.order(account=conta, order_id="2000001")
        adap.shipment_costs(account=conta, shipment_id=44001)
        self.assertTrue(pedidos_http[0].startswith("/orders/search?seller=96417426&order.status=paid"))
        self.assertIn("sort=date_desc", pedidos_http[0])
        self.assertEqual(pedidos_http[1:], ["/orders/2000001", "/shipments/44001/costs"])
