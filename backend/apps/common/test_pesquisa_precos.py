"""Spec 013 — pesquisa no Mercado Livre: produtos e mais vendidos. Só leitura, sem rede.

As respostas de mentira seguem o formato visto na primeira pesquisa real (25/09/2026):
produto do catálogo com `permalink` vazio, foto em `pickers` e sem vendedor ganhando a página.
"""

from contextlib import contextmanager
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.integrations import base
from apps.integrations.base import IntegrationError
from apps.integrations.meli import pesquisa
from apps.integrations.models import MarketplaceAccount

PRODUTO_REAL = {
    "id": "MLB19713494", "catalog_product_id": "MLB19713494", "status": "active",
    "pdp_types": ["traditional"], "domain_id": "MLB-MOBILE_DEVICE_CHARGERS", "permalink": "",
    "name": "Carregador Turbo USB-C 20W Hrebos Branco Compatível Samsung Galaxy",
    "family_name": "Carregador Hrebos HS-363C usb-c com cabo carregamento turbo",
    "type": "catalog_product", "buy_box_winner": None,
    "attributes": [{"id": "BRAND", "value_name": "Hrebos"}, {"id": "MODEL", "value_name": "HS-363C"}],
    "pickers": [{"picker_id": "COLOR", "products": [
        {"product_id": "MLB0000", "thumbnail": "https://http2.mlstatic.com/outra.jpg"},
        {"product_id": "MLB19713494", "thumbnail": "https://http2.mlstatic.com/branco.jpg"},
    ]}],
}


class Pesquisador:
    """Mercado Livre de mentira."""

    channel = "mercado_livre"
    chamadas = []

    def search_catalog(self, *, account, q="", gtin="", limit=10):
        Pesquisador.chamadas.append(("search_catalog", q or gtin))
        return [{"id": "MLB19713494", "name": "Carregador"}]

    def product(self, *, account, product_id):
        Pesquisador.chamadas.append(("product", product_id))
        if product_id == "MLB19713494":
            return PRODUTO_REAL
        return {"id": product_id, "name": "Fone Bluetooth", "permalink": "https://www.mercadolivre.com.br/p/MLB333"}

    def best_sellers(self, *, account, category_id):
        Pesquisador.chamadas.append(("best_sellers", category_id))
        return [
            {"id": "MLBU1", "position": 3, "type": "USER_PRODUCT"},
            {"id": "MLB333", "position": 2, "type": "PRODUCT"},
            {"id": "MLB500", "position": 1, "type": "ITEM"},
        ]

    def items(self, *, account, ids):
        Pesquisador.chamadas.append(("items", tuple(ids)))
        return [{"id": "MLB500", "title": "Suporte de celular",
                 "permalink": "https://produto.mercadolivre.com.br/MLB-500",
                 "pictures": [{"secure_url": "https://http2.mlstatic.com/suporte.jpg"}]}]

    recusar_user_product = False

    def user_product(self, *, account, user_product_id):
        Pesquisador.chamadas.append(("user_product", user_product_id))
        if Pesquisador.recusar_user_product:
            # resposta real: 'caller is not allowed to access this user product'
            raise IntegrationError("O Mercado Livre não liberou esta consulta para a sua conta (HTTP 403).")
        return {"id": user_product_id, "name": "Luminária 3D"}


@contextmanager
def mercado_livre_pesquisando():
    original = base._ADAPTADORES.get("mercado_livre")
    Pesquisador.chamadas, Pesquisador.recusar_user_product = [], False
    base._ADAPTADORES["mercado_livre"] = Pesquisador
    try:
        yield Pesquisador
    finally:
        base._ADAPTADORES["mercado_livre"] = original


class Conta(TestCase):
    def setUp(self):
        MarketplaceAccount.objects.create(
            channel="mercado_livre", external_id="96417426", active=True,
            access_token="tok", refresh_token="ref",
            token_expires_at=timezone.now() + timedelta(hours=5),
        )


class RegrasTests(TestCase):
    def test_link_usa_permalink_ou_a_busca_do_site(self):
        self.assertEqual(pesquisa.link({"permalink": "https://x/p/1"}, "a"), "https://x/p/1")
        self.assertEqual(
            pesquisa.link({"permalink": ""}, "Carregador  Hrebos HS-363C"),
            "https://lista.mercadolivre.com.br/Carregador-Hrebos-HS-363C",
        )
        self.assertEqual(pesquisa.link({}, ""), "")


class PesquisaTests(Conta):
    def test_produtos_com_marca_modelo_foto_e_link(self):
        with mercado_livre_pesquisando():
            r = pesquisa.produtos(q="carregador 20w")
        p = r[0]
        self.assertEqual((p["marca"], p["modelo"]), ("Hrebos", "HS-363C"))
        self.assertEqual(p["foto"], "https://http2.mlstatic.com/branco.jpg")  # a variação do próprio produto
        self.assertTrue(p["link"].startswith("https://lista.mercadolivre.com.br/Carregador-Hrebos"))
        self.assertNotIn("preco", p)  # preço de concorrente não vem pela API: não é prometido

    def test_mais_vendidos_na_ordem_e_completados_por_tipo(self):
        with mercado_livre_pesquisando() as ml:
            r = pesquisa.mais_vendidos("MLB1234")
        itens = r["itens"]
        self.assertEqual([i["posicao"] for i in itens], [1, 2, 3])
        self.assertEqual(itens[0]["nome"], "Suporte de celular")
        self.assertEqual(itens[0]["link"], "https://produto.mercadolivre.com.br/MLB-500")
        self.assertEqual(itens[1]["nome"], "Fone Bluetooth")
        self.assertEqual(itens[2]["nome"], "Luminária 3D")
        self.assertIn(("items", ("MLB500",)), ml.chamadas)  # anúncios numa chamada só

    def test_item_recusado_nao_derruba_a_lista(self):
        with mercado_livre_pesquisando() as ml:
            ml.recusar_user_product = True
            r = pesquisa.mais_vendidos("MLB1000")
        itens = r["itens"]
        self.assertEqual(len(itens), 3)
        self.assertEqual(itens[2]["nome"], "Produto de outro vendedor (detalhes não liberados)")
        self.assertEqual(itens[2]["link"], "")
        self.assertEqual(itens[0]["nome"], "Suporte de celular")  # os outros seguem normais

    def test_so_leitura(self):
        with mercado_livre_pesquisando() as ml:
            pesquisa.mais_vendidos("MLB1234")
            pesquisa.produtos(gtin="7891234567890")
        self.assertEqual(
            {nome for nome, _ in ml.chamadas},
            {"best_sellers", "items", "product", "user_product", "search_catalog"},
        )


class ApiTests(Conta):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user("pesquisa")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def permitir(self, *codenames):
        self.user.user_permissions.set(Permission.objects.filter(codename__in=codenames))
        self.user = get_user_model().objects.get(pk=self.user.pk)
        self.client.force_authenticate(self.user)

    def test_exige_permissao_de_ver_integracoes(self):
        with mercado_livre_pesquisando() as ml:
            r = self.client.get("/api/v1/integrations/price-best-sellers/?category_id=MLB1234")
        self.assertEqual(r.status_code, 403)
        self.assertEqual(ml.chamadas, [])

    def test_rotas_e_validacao(self):
        self.permitir("view_marketplaceaccount")
        with mercado_livre_pesquisando() as ml:
            self.assertEqual(self.client.get("/api/v1/integrations/price-products/?q=ab").status_code, 400)
            self.assertEqual(self.client.get("/api/v1/integrations/price-products/?gtin=12a").status_code, 400)
            self.assertEqual(
                self.client.get("/api/v1/integrations/price-best-sellers/?category_id=../x").status_code, 400
            )
            self.assertEqual(ml.chamadas, [])
            r = self.client.get("/api/v1/integrations/price-products/?gtin=7891234567890")
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json()["produtos"][0]["id"], "MLB19713494")
            r = self.client.get("/api/v1/integrations/price-best-sellers/?category_id=MLB1234")
            self.assertEqual(len(r.json()["itens"]), 3)
        self.assertEqual(self.client.get("/api/v1/integrations/price-offers/?product_id=MLB1").status_code, 404)

    def test_sem_conta_vira_400_legivel(self):
        MarketplaceAccount.objects.all().delete()
        self.permitir("view_marketplaceaccount")
        with mercado_livre_pesquisando():
            r = self.client.get("/api/v1/integrations/price-best-sellers/?category_id=MLB1234")
        self.assertEqual(r.status_code, 400)
        self.assertIn("Conecte uma conta", str(r.json()))


class ClientePesquisaTests(Conta):
    """O cliente real, com o transporte HTTP trocado por respostas gravadas."""

    def adaptador(self, *respostas):
        from apps.integrations.meli.cliente import HttpResponse, MercadoLivreAdapter

        self.pedidos, fila = [], list(respostas)

        def transporte(method, path, **kwargs):
            self.pedidos.append((method, path))
            status, body = fila.pop(0)
            return HttpResponse(status, body, {})

        return MercadoLivreAdapter(transporte=transporte, config={
            "client_id": "1", "client_secret": "s", "redirect_uri": "https://x/cb",
        })

    def test_caminhos_da_documentacao(self):
        conta = MarketplaceAccount.objects.get()
        adap = self.adaptador(
            (200, {"results": [{"id": "MLB1"}]}),
            (200, {"content": [{"id": "MLB2", "type": "ITEM"}]}),
            (200, [{"code": 200, "body": {"id": "MLB2", "title": "x"}}, {"code": 404, "body": {"id": "MLB3"}}]),
        )
        self.assertEqual(adap.search_catalog(account=conta, gtin="789"), [{"id": "MLB1"}])
        self.assertEqual(adap.best_sellers(account=conta, category_id="MLB9")[0]["id"], "MLB2")
        self.assertEqual(adap.items(account=conta, ids=["MLB2", "MLB3"]), [{"id": "MLB2", "title": "x"}])
        caminhos = [p for _, p in self.pedidos]
        self.assertIn("product_identifier=789", caminhos[0])
        self.assertTrue(caminhos[0].startswith("/products/search?status=active&site_id=MLB"))
        self.assertEqual(caminhos[1], "/highlights/MLB/category/MLB9")
        self.assertEqual(caminhos[2], "/items/bulk?ids=MLB2%2CMLB3")
