"""Contrato local do Mercado Livre, sem conta real nem chamadas de rede."""

from contextlib import contextmanager
from datetime import timedelta
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.catalog.models import Product
from apps.integrations import base, services
from apps.integrations.base import IntegrationError
from apps.integrations.meli.cliente import HttpResponse, MercadoLivreAdapter
from apps.integrations.models import Listing, MarketplaceAccount, OAuthAttempt, OutboxEvent
from apps.inventory.models import Stock

CONFIG = {
    "client_id": "app-local", "client_secret": "secret-local",
    "redirect_uri": "https://exemplo.test/jalapao-store/callback", "pkce_enabled": True,
}


class Gravador:
    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.chamadas = []

    def __call__(self, method, path, **kwargs):
        self.chamadas.append((method, path, kwargs))
        return self.respostas.pop(0)


def resposta(body, status=200, headers=None):
    return HttpResponse(status, body, headers or {})


@contextmanager
def usando(adapter):
    original = base._ADAPTADORES["mercado_livre"]
    base._ADAPTADORES["mercado_livre"] = lambda: adapter
    try:
        yield
    finally:
        base._ADAPTADORES["mercado_livre"] = original


class OAuthTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("dono")
        self.other = get_user_model().objects.create_user("outro")
        self.gravador = Gravador([resposta({
            "access_token": "acesso", "refresh_token": "novo-refresh",
            "expires_in": 21600, "user_id": 1234,
        })])
        self.adapter = MercadoLivreAdapter(transporte=self.gravador, config=CONFIG)

    def test_state_pkce_e_callback_de_uso_unico(self):
        with usando(self.adapter):
            url = services.iniciar_oauth_ml(self.user)
            query = parse_qs(urlparse(url).query)
            state = query["state"][0]
            self.assertEqual(query["code_challenge_method"], ["S256"])
            self.assertEqual(query["redirect_uri"], [CONFIG["redirect_uri"]])
            self.assertNotEqual(OAuthAttempt.objects.get().state_hash, state)
            with self.assertRaises(IntegrationError):
                services.conectar_ml(user=self.other, code="codigo", state=state)
            conta = services.conectar_ml(user=self.user, code="codigo", state=state)
            self.assertEqual(conta.external_id, "1234")
            self.assertEqual(conta.refresh_token, "novo-refresh")
            self.assertEqual(self.gravador.chamadas[0][2]["data"]["code_verifier"],
                             OAuthAttempt.objects.get().code_verifier)
            with self.assertRaises(IntegrationError):
                services.conectar_ml(user=self.user, code="codigo", state=state)
            self.assertEqual(len(self.gravador.chamadas), 1)

    def test_expirado_ou_ausente_nao_troca_codigo(self):
        with usando(self.adapter):
            url = services.iniciar_oauth_ml(self.user)
            state = parse_qs(urlparse(url).query)["state"][0]
            OAuthAttempt.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
            for bad in (state, "inexistente"):
                with self.assertRaises(IntegrationError):
                    services.conectar_ml(user=self.user, code="x", state=bad)
        self.assertEqual(self.gravador.chamadas, [])

    def test_refresh_guarda_novo_token_e_rejeita_usuario_diferente(self):
        conta = MarketplaceAccount.objects.create(
            channel="mercado_livre", external_id="1234", access_token="antigo",
            refresh_token="refresh-antigo", token_expires_at=timezone.now() - timedelta(hours=1),
        )
        with usando(self.adapter):
            services.renovar(conta)
        self.assertEqual(conta.refresh_token, "novo-refresh")
        self.assertEqual(self.gravador.chamadas[0][2]["data"]["refresh_token"], "refresh-antigo")
        self.assertTrue(conta.token_valido)


class CatalogoEstoqueTests(TestCase):
    def setUp(self):
        self.conta = MarketplaceAccount.objects.create(
            channel="mercado_livre", external_id="1234", access_token="acesso",
            refresh_token="refresh", token_expires_at=timezone.now() + timedelta(hours=2),
        )
        self.produto = Product.objects.create(sku="SKU-1", name="Peça")
        Stock.objects.create(product=self.produto, quantity=7)

    def test_importacao_por_sku_e_variacao_ambigua(self):
        gravador = Gravador([
            resposta({"results": ["MLB1", "MLB2"], "paging": {"total": 2}}),
            resposta([
                {"status_code": 200, "body": {"id": "MLB1", "seller_id": 1234,
                 "title": "Peça", "seller_custom_field": "SKU-1", "available_quantity": 3,
                 "user_product_id": "MLBU1"}},
                {"status_code": 200, "body": {"id": "MLB2", "seller_id": 1234,
                 "title": "Variação", "seller_custom_field": "SKU-1", "variations": [{"id": 1}]}},
            ]),
        ])
        with usando(MercadoLivreAdapter(transporte=gravador, config=CONFIG)):
            result = services.importar_anuncios(self.conta)
        self.assertEqual(result["total"], 2)
        self.assertEqual(len(result["pendentes"]), 1)
        self.assertEqual(Listing.objects.count(), 1)
        vinculo = Listing.objects.get()
        self.assertEqual(vinculo.user_product_id, "MLBU1")
        self.assertFalse(vinculo.sync_enabled)
        self.assertEqual(Stock.objects.get(product=self.produto).quantity, 7)

    def test_envio_manual_usa_saldo_atual_sem_consumir_outbox(self):
        Listing.objects.create(product=self.produto, marketplace="mercado_livre",
                               seller_id="1234", item_id="MLB1", sync_enabled=True)
        evento = OutboxEvent.objects.create(topic="inventory.changed", payload={
            "product_id": str(self.produto.pk), "quantity": 1,
        })
        gravador = Gravador([
            resposta({"id": "MLB1", "seller_id": 1234, "shipping": {"logistic_type": "drop_off"}}),
            resposta({"id": 1234, "tags": []}),
            resposta({"id": "MLB1"}),
        ])
        with usando(MercadoLivreAdapter(transporte=gravador, config=CONFIG)):
            result = services.enviar_estoque(self.conta)
        self.assertEqual(result["enviados"], 1)
        self.assertEqual(gravador.chamadas[-1][2]["data"], {"available_quantity": 7})
        evento.refresh_from_db()
        self.assertIsNone(evento.delivered_at)

    def test_deposito_multiplo_e_full_recusados_sem_put(self):
        for item, other_responses in [
            ({"id": "MLB1", "seller_id": 1234, "user_product_id": "MLBU1"}, [
                resposta({"tags": ["warehouse_management"]}),
                resposta({"locations": [
                    {"type": "seller_warehouse", "store_id": "1", "network_node_id": "N1"},
                    {"type": "seller_warehouse", "store_id": "2", "network_node_id": "N2"},
                ]}, headers={"x-version": "4"}),
            ]),
            ({"id": "MLB1", "seller_id": 1234,
              "shipping": {"logistic_type": "fulfillment"}}, []),
        ]:
            gravador = Gravador([resposta(item), *other_responses])
            with self.assertRaises(IntegrationError), usando(
                MercadoLivreAdapter(transporte=gravador, config=CONFIG)
            ):
                base.adaptador("mercado_livre").update_stock(
                    account=self.conta, item_id="MLB1", quantity=7,
                )
            self.assertFalse(any(method == "PUT" for method, _, _ in gravador.chamadas))

    def test_deposito_unico_envia_com_versao_e_localizacao(self):
        gravador = Gravador([
            resposta({"id": "MLB1", "seller_id": 1234, "user_product_id": "MLBU1"}),
            resposta({"tags": ["warehouse_management"]}),
            resposta({"locations": [{"type": "seller_warehouse", "store_id": "1",
                                      "network_node_id": "N1", "quantity": 3}]},
                     headers={"X-Version": "5"}),
            resposta({"id": "MLBU1"}),
        ])
        adapter = MercadoLivreAdapter(transporte=gravador, config=CONFIG)
        adapter.update_stock(account=self.conta, item_id="MLB1", quantity=7)
        method, path, kwargs = gravador.chamadas[-1]
        self.assertEqual(method, "PUT")
        self.assertEqual(path, "/user-products/MLBU1/stock/type/seller_warehouse")
        self.assertEqual(kwargs["headers"], {"x-version": "5"})
        self.assertEqual(kwargs["data"]["locations"], [{
            "store_id": "1", "network_node_id": "N1", "quantity": 7,
        }])


class ApiTests(TestCase):
    def test_auth_link_requer_permissao_e_metodo_post(self):
        user = get_user_model().objects.create_user("dono")
        client = APIClient()
        client.force_authenticate(user)
        url = "/api/v1/integrations/ml-auth-link/"
        self.assertEqual(client.post(url, {}, format="json").status_code, 403)
        user.user_permissions.add(*Permission.objects.filter(
            codename__in=["change_marketplaceaccount", "view_marketplaceaccount"],
        ))
        self.assertNotEqual(client.get(url).status_code, 200)
        self.assertFalse(OAuthAttempt.objects.exists())

    def test_oauth_api_conecta_sem_external_id_do_navegador(self):
        user = get_user_model().objects.create_user("dono")
        user.user_permissions.add(*Permission.objects.filter(
            codename__in=["change_marketplaceaccount", "view_marketplaceaccount"],
        ))
        client = APIClient()
        client.force_authenticate(user)
        gravador = Gravador([resposta({
            "access_token": "acesso", "refresh_token": "refresh",
            "expires_in": 21600, "user_id": 1234,
        })])
        with usando(MercadoLivreAdapter(transporte=gravador, config=CONFIG)):
            link = client.post("/api/v1/integrations/ml-auth-link/", {}, format="json")
            self.assertEqual(link.status_code, 200)
            state = parse_qs(urlparse(link.json()["url"]).query)["state"][0]
            erro = client.post("/api/v1/integrations/connect/", {
                "channel": "mercado_livre", "code": "codigo", "state": "errado",
            }, format="json")
            self.assertEqual(erro.status_code, 400)
            resposta_api = client.post("/api/v1/integrations/connect/", {
                "channel": "mercado_livre", "code": "codigo", "state": state,
            }, format="json")
        self.assertEqual(resposta_api.status_code, 200)
        self.assertEqual(resposta_api.json()["external_id"], "1234")
        self.assertNotIn("refresh_token", resposta_api.json())
