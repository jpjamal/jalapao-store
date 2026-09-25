"""Spec 013 — pesquisa de preços no Mercado Livre. Só leitura, sem rede nos testes."""

from contextlib import contextmanager
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.integrations import base
from apps.integrations.meli import pesquisa
from apps.integrations.models import MarketplaceAccount


class Pesquisador:
    """Mercado Livre de mentira, com respostas no formato da documentação."""

    channel = "mercado_livre"
    chamadas = []

    def search_catalog(self, *, account, q="", gtin="", limit=10):
        Pesquisador.chamadas.append(("search_catalog", q or gtin))
        return [{"id": "MLB111", "name": "Carregador Turbo 20W"}, {"id": "MLB222", "name": "Sem preço"}]

    def product(self, *, account, product_id):
        Pesquisador.chamadas.append(("product", product_id))
        if product_id == "MLB111":
            return {
                "id": "MLB111", "name": "Carregador Turbo 20W USB-C",
                "permalink": "https://www.mercadolivre.com.br/p/MLB111",
                "attributes": [{"id": "BRAND", "value_name": "Baseus"}, {"id": "MODEL", "value_name": "T20"}],
                "pictures": [{"secure_url": "https://http2.mlstatic.com/foto.jpg"}],
                "buy_box_winner": {"price": 49.9, "shipping": {"free_shipping": True}},
            }
        if product_id == "MLB333":
            return {"id": "MLB333", "name": "Fone Bluetooth", "buy_box_winner": {"price": 89}}
        return {"id": product_id, "name": "Sem preço"}

    def product_items(self, *, account, product_id, limit=20):
        Pesquisador.chamadas.append(("product_items", product_id))
        return [
            {"item_id": "MLB9", "price": 59.9, "seller_id": 3, "condition": "new",
             "shipping": {"free_shipping": True, "logistic_type": "fulfillment"}},
            {"item_id": "MLB8", "price": 45.0, "seller_id": 2, "condition": "new", "shipping": {}},
            {"item_id": "MLB7", "price": 52.5, "seller_id": 1, "condition": "new", "shipping": {}},
        ]

    def best_sellers(self, *, account, category_id):
        Pesquisador.chamadas.append(("best_sellers", category_id))
        return [
            {"id": "MLBU1", "position": 3, "type": "USER_PRODUCT"},
            {"id": "MLB333", "position": 2, "type": "PRODUCT"},
            {"id": "MLB500", "position": 1, "type": "ITEM"},
        ]

    def items(self, *, account, ids):
        Pesquisador.chamadas.append(("items", tuple(ids)))
        return [{"id": "MLB500", "title": "Suporte de celular", "price": 19.9,
                 "permalink": "https://produto.mercadolivre.com.br/MLB-500"}]

    def user_product(self, *, account, user_product_id):
        Pesquisador.chamadas.append(("user_product", user_product_id))
        return {"id": user_product_id, "name": "Luminária 3D"}


@contextmanager
def mercado_livre_pesquisando():
    original = base._ADAPTADORES.get("mercado_livre")
    Pesquisador.chamadas = []
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
    def test_preco_nos_formatos_conhecidos(self):
        self.assertEqual(pesquisa.preco_de({"price": 10}), 10.0)
        self.assertEqual(pesquisa.preco_de({"price": {"amount": "12.5"}}), 12.5)
        self.assertEqual(pesquisa.preco_de({"sale_price": {"amount": 7}}), 7.0)
        self.assertEqual(pesquisa.preco_de({"buy_box_winner": {"price": 3}}), 3.0)
        self.assertIsNone(pesquisa.preco_de({"name": "x"}))
        self.assertIsNone(pesquisa.preco_de(None))

    def test_resumo_ignora_sem_preco(self):
        self.assertEqual(
            pesquisa.resumo([30, None, 10, 20]),
            {"quantidade": 3, "menor": 10, "mediana": 20, "maior": 30},
        )
        self.assertEqual(pesquisa.resumo([None])["quantidade"], 0)


class PesquisaTests(Conta):
    def test_produtos_com_preco_vencedor(self):
        with mercado_livre_pesquisando(), self.assertLogs("apps.integrations.meli.pesquisa", "WARNING"):
            r = pesquisa.produtos(q="carregador 20w")
        self.assertEqual(r[0]["preco_vencedor"], 49.9)
        self.assertEqual((r[0]["marca"], r[0]["modelo"]), ("Baseus", "T20"))
        self.assertTrue(r[0]["frete_gratis"])
        self.assertIsNone(r[1]["preco_vencedor"])  # sem preço: fica vazio e vai para o log

    def test_ofertas_da_mais_barata_para_a_mais_cara(self):
        with mercado_livre_pesquisando():
            r = pesquisa.ofertas("MLB111")
        self.assertEqual([o["preco"] for o in r["ofertas"]], [45.0, 52.5, 59.9])
        self.assertEqual(r["resumo"], {"quantidade": 3, "menor": 45.0, "mediana": 52.5, "maior": 59.9})
        self.assertTrue(r["ofertas"][2]["full"])

    def test_mais_vendidos_completa_nome_e_preco_por_tipo(self):
        with mercado_livre_pesquisando() as ml, self.assertLogs("apps.integrations.meli.pesquisa", "WARNING"):
            r = pesquisa.mais_vendidos("MLB1234")
        self.assertEqual([i["posicao"] for i in r["itens"]], [1, 2, 3])
        self.assertEqual((r["itens"][0]["nome"], r["itens"][0]["preco"]), ("Suporte de celular", 19.9))
        self.assertEqual((r["itens"][1]["nome"], r["itens"][1]["preco"]), ("Fone Bluetooth", 89.0))
        self.assertEqual(r["itens"][2]["nome"], "Luminária 3D")
        self.assertIsNone(r["itens"][2]["preco"])
        self.assertIn(("items", ("MLB500",)), ml.chamadas)  # anúncios numa chamada só

    def test_nada_e_gravado_nem_enviado(self):
        with mercado_livre_pesquisando() as ml:
            pesquisa.ofertas("MLB111")
        operacoes = {nome for nome, _ in ml.chamadas}
        self.assertEqual(operacoes, {"product_items"})


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
            r = self.client.get("/api/v1/integrations/price-offers/?product_id=MLB111")
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
            with self.assertLogs("apps.integrations.meli.pesquisa", "WARNING"):
                r = self.client.get("/api/v1/integrations/price-products/?gtin=7891234567890")
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json()["produtos"][0]["id"], "MLB111")
            r = self.client.get("/api/v1/integrations/price-offers/?product_id=MLB111")
            self.assertEqual(r.json()["resumo"]["menor"], 45.0)

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
            (200, {"results": []}),
            (200, {"content": [{"id": "MLB2", "type": "ITEM"}]}),
            (200, [{"code": 200, "body": {"id": "MLB2", "price": 5}}, {"code": 404, "body": {"id": "MLB3"}}]),
        )
        self.assertEqual(adap.search_catalog(account=conta, gtin="789"), [{"id": "MLB1"}])
        self.assertEqual(adap.product_items(account=conta, product_id="MLB1"), [])
        self.assertEqual(adap.best_sellers(account=conta, category_id="MLB9")[0]["id"], "MLB2")
        self.assertEqual(adap.items(account=conta, ids=["MLB2", "MLB3"]), [{"id": "MLB2", "price": 5}])
        caminhos = [p for _, p in self.pedidos]
        self.assertIn("product_identifier=789", caminhos[0])
        self.assertTrue(caminhos[0].startswith("/products/search?status=active&site_id=MLB"))
        self.assertTrue(caminhos[1].startswith("/products/MLB1/items?limit="))
        self.assertEqual(caminhos[2], "/highlights/MLB/category/MLB9")
        self.assertEqual(caminhos[3], "/items/bulk?ids=MLB2%2CMLB3")
