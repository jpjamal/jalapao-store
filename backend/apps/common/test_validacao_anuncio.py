"""Spec 011 — validar rascunho contra o Mercado Livre sem publicar.

O adaptador do Mercado Livre é trocado por um falso que registra toda chamada. Assim dá
para provar o que importa sem rede: quais regras bloqueiam, quais só avisam, o que vai no
envio da simulação — e que nenhuma chamada de criação de anúncio acontece.
"""

from contextlib import contextmanager
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.catalog.models import ListingDraft, ListingDraftImage, Product, ProductImage
from apps.integrations import base
from apps.integrations.meli import anuncio
from apps.integrations.models import Listing, MarketplaceAccount
from apps.inventory.models import Stock

CATEGORIA = {
    "id": "MLB1234",
    "name": "Luminárias",
    "path_from_root": [{"name": "Casa"}, {"name": "Iluminação"}, {"name": "Luminárias"}],
    "settings": {
        "listing_allowed": True,
        "max_title_length": 60,
        "max_pictures_per_item": 3,
        "minimum_price": 8,
    },
}
ATRIBUTOS = [
    {"id": "BRAND", "name": "Marca", "tags": {"required": True}, "value_type": "string"},
    {"id": "MODEL", "name": "Modelo", "tags": ["required", "catalog_required"], "value_type": "string"},
    {"id": "VOLTAGE", "name": "Voltagem", "tags": {"required": True}, "value_type": "list",
     "values": [{"id": "1", "name": "110V"}, {"id": "2", "name": "220V"}]},
    {"id": "GTIN", "name": "Código universal", "tags": {"conditional_required": True, "hidden": True}},
    {"id": "PACKAGE_HEIGHT", "name": "Altura do pacote", "tags": {"read_only": True, "required": True}},
    {"id": "COLOR", "name": "Cor", "tags": {}, "value_type": "list"},
]


class Falso:
    """Adaptador do Mercado Livre de mentira. `causas` é o que a simulação devolve."""

    channel = "mercado_livre"
    chamadas = []
    causas = []
    ultimo_envio = None

    def suggest_categories(self, *, account, q, limit=3):
        Falso.chamadas.append(("suggest_categories", q))
        return [{"category_id": "MLB1234", "category_name": "Luminárias", "domain_name": "Luminárias"}]

    def site_categories(self, *, account):
        Falso.chamadas.append(("site_categories", ""))
        return [{"id": "MLB1574", "name": "Casa"}, {"id": "MLB1132", "name": "Brinquedos"}]

    def category(self, *, account, category_id):
        Falso.chamadas.append(("category", category_id))
        if category_id == "MLB1574":
            return {"id": "MLB1574", "name": "Casa", "path_from_root": [{"id": "MLB1574", "name": "Casa"}],
                    "children_categories": [{"id": "MLB1234", "name": "Luminárias"}],
                    "settings": {"listing_allowed": True}}
        return CATEGORIA

    def category_attributes(self, *, account, category_id):
        Falso.chamadas.append(("category_attributes", category_id))
        return ATRIBUTOS

    def validate_item(self, *, account, payload):
        Falso.chamadas.append(("validate_item", payload.get("title")))
        Falso.ultimo_envio = payload
        return list(Falso.causas)


@contextmanager
def mercado_livre_falso(causas=()):
    original = base._ADAPTADORES.get("mercado_livre")
    Falso.chamadas, Falso.causas, Falso.ultimo_envio = [], list(causas), None
    base._ADAPTADORES["mercado_livre"] = Falso
    try:
        yield Falso
    finally:
        base._ADAPTADORES["mercado_livre"] = original


class Base(TestCase):
    def setUp(self):
        MarketplaceAccount.objects.create(
            channel="mercado_livre", external_id="96417426", active=True,
            access_token="tok", refresh_token="ref",
            token_expires_at=timezone.now() + timedelta(hours=5),
        )
        self.produto = Product.objects.create(name="Luminária Pimentão", cost_price=Decimal("12.34"))
        Stock.objects.create(product=self.produto, quantity=5, value=Decimal("61.70"))

    def foto(self, mime="image/jpeg", w=1200, h=1200):
        return ProductImage.objects.create(
            product=self.produto, file="produtos/x.jpg", mime_type=mime,
            width=w, height=h, size_bytes=1000,
        )

    def rascunho(self, fotos=(), **campos):
        dados = dict(
            product=self.produto, channel="mercado_livre", title="Luminária Pimentão 3D",
            description="Peça impressa em 3D.", price=Decimal("59.90"), brand="Jalapão",
            model="Pimentão", condition="new", category_id="MLB1234",
            attributes={"VOLTAGE": {"value_id": "1", "value_name": "110V"}},
        )
        dados.update(campos)
        d = ListingDraft.objects.create(**dados)
        for posicao, f in enumerate(fotos):
            ListingDraftImage.objects.create(draft=d, image=f, position=posicao)
        return d


class TagsEFormularioTests(TestCase):
    def test_tags_como_objeto_ou_lista(self):
        self.assertEqual(anuncio.tags_de({"tags": {"required": True, "hidden": False}}), {"required"})
        self.assertEqual(anuncio.tags_de({"tags": ["required", "catalog_required"]}),
                         {"required", "catalog_required"})
        self.assertEqual(anuncio.tags_de({}), set())

    def test_formulario_sem_ocultos_e_obrigatorios_primeiro(self):
        form = anuncio.atributos_do_formulario(ATRIBUTOS)
        ids = [a["id"] for a in form]
        self.assertNotIn("GTIN", ids)            # oculto
        self.assertNotIn("PACKAGE_HEIGHT", ids)  # somente leitura
        self.assertEqual(ids[-1], "COLOR")       # opcional por último
        self.assertTrue(all(a["required"] for a in form[:3]))
        voltagem = next(a for a in form if a["id"] == "VOLTAGE")
        self.assertEqual([v["name"] for v in voltagem["values"]], ["110V", "220V"])


class DiagnosticoTests(Base):
    def test_rascunho_vazio_da_erros_basicos_sem_simular(self):
        d = self.rascunho(title="", price=None, category_id="", brand="", model="", attributes={})
        with mercado_livre_falso() as falso:
            r = anuncio.diagnosticar(d)
        campos = {e["campo"] for e in r["erros"]}
        self.assertTrue({"title", "price", "category_id", "images"} <= campos)
        self.assertFalse(r["pode_publicar"])
        self.assertFalse(r["simulado_no_mercado_livre"])
        self.assertEqual(falso.chamadas, [])  # sem categoria não há o que perguntar

    def test_rascunho_completo_e_valido_pode_publicar(self):
        d = self.rascunho(fotos=[self.foto()])
        with mercado_livre_falso(causas=[]) as falso:
            r = anuncio.diagnosticar(d)
        self.assertEqual(r["erros"], [])
        self.assertTrue(r["simulado_no_mercado_livre"])
        self.assertTrue(r["pode_publicar"])
        self.assertEqual(r["categoria"]["caminho"], ["Casa", "Iluminação", "Luminárias"])
        envio = falso.ultimo_envio
        self.assertEqual(envio["currency_id"], "BRL")
        self.assertEqual(envio["price"], 59.9)
        self.assertEqual(envio["available_quantity"], 5)
        self.assertNotIn("pictures", envio)
        ids = {a["id"] for a in envio["attributes"]}
        self.assertEqual(ids, {"BRAND", "MODEL", "VOLTAGE"})
        # custo interno nunca sai
        self.assertNotIn("12.34", str(envio))

    def test_nenhuma_chamada_de_criacao(self):
        d = self.rascunho(fotos=[self.foto()])
        with mercado_livre_falso() as falso:
            anuncio.diagnosticar(d)
        operacoes = {nome for nome, _ in falso.chamadas}
        self.assertEqual(operacoes, {"category", "category_attributes", "validate_item"})
        self.assertEqual(Listing.objects.count(), 0)

    def test_erro_do_mercado_livre_bloqueia_aviso_nao(self):
        d = self.rascunho(fotos=[self.foto()])
        causas = [
            {"type": "warning", "code": "shipping.me2_adoption_mandatory",
             "references": ["shipping.modes"], "message": "ME2 adoption is mandatory"},
        ]
        with mercado_livre_falso(causas=causas):
            r = anuncio.diagnosticar(d)
        self.assertTrue(r["pode_publicar"])
        self.assertEqual(r["avisos"][-1]["origem"], "mercado_livre")

        causas.append({"type": "error", "code": "moderations.seller.not_authorized",
                       "references": ["item.category_id"], "message": "Seller is not authorized"})
        with mercado_livre_falso(causas=causas):
            r = anuncio.diagnosticar(d)
        self.assertFalse(r["pode_publicar"])
        self.assertEqual(r["erros"][0]["codigo"], "moderations.seller.not_authorized")

    def test_causa_de_foto_e_retirada_porque_a_simulacao_vai_sem_fotos(self):
        d = self.rascunho(fotos=[self.foto()])
        causas = [{"type": "error", "code": "item.listing_type_id.requiresPictures",
                   "references": ["item.pictures"], "message": "Item pictures are mandatory"}]
        with mercado_livre_falso(causas=causas):
            r = anuncio.diagnosticar(d)
        self.assertTrue(r["pode_publicar"])
        self.assertEqual(r["causas_de_foto_retiradas"], 1)

    def test_fotos_webp_e_pequenas(self):
        d = self.rascunho(fotos=[self.foto("image/webp"), self.foto(w=400, h=400), self.foto(w=800, h=900)])
        with mercado_livre_falso():
            r = anuncio.diagnosticar(d)
        erros = [e["mensagem"] for e in r["erros"] if e["campo"] == "images"]
        avisos = [a["mensagem"] for a in r["avisos"] if a["campo"] == "images"]
        self.assertTrue(any("webp" in e for e in erros))
        self.assertTrue(any("400×400" in a and "não amplia" in a for a in avisos))
        self.assertTrue(any("800×900" in a and "recomendado" in a for a in avisos))

    def test_fotos_acima_do_maximo_da_categoria(self):
        d = self.rascunho(fotos=[self.foto() for _ in range(4)])
        with mercado_livre_falso():
            r = anuncio.diagnosticar(d)
        self.assertTrue(any("aceita até 3" in e["mensagem"] for e in r["erros"]))

    def test_atributo_obrigatorio_vazio_e_erro_oculto_nunca_e_exigido(self):
        d = self.rascunho(fotos=[self.foto()], attributes={})
        with mercado_livre_falso():
            r = anuncio.diagnosticar(d)
        campos = {e["campo"] for e in r["erros"]}
        self.assertIn("attributes.VOLTAGE", campos)
        self.assertNotIn("attributes.PACKAGE_HEIGHT", campos)  # obrigatório, mas somente leitura
        self.assertNotIn("attributes.GTIN", {a["campo"] for a in r["avisos"]})  # oculto

    def test_titulo_e_preco_nos_limites_da_categoria(self):
        d = self.rascunho(fotos=[self.foto()], title="x" * 61, price=Decimal("5"))
        with mercado_livre_falso():
            r = anuncio.diagnosticar(d)
        msgs = " ".join(e["mensagem"] for e in r["erros"])
        self.assertIn("aceita até 60", msgs)
        self.assertIn("preço mínimo", msgs)

    def test_estoque_zero_avisa_e_simula_com_uma_unidade(self):
        Stock.objects.filter(product=self.produto).update(quantity=0, value=0)
        d = self.rascunho(fotos=[self.foto()])
        # recarrega do banco, como a API faz: o produto em memória guardou o estoque antigo
        d = ListingDraft.objects.get(pk=d.pk)
        with mercado_livre_falso() as falso:
            r = anuncio.diagnosticar(d)
        self.assertTrue(any(a["campo"] == "stock" for a in r["avisos"]))
        self.assertEqual(falso.ultimo_envio["available_quantity"], 1)

    def test_sem_conta_do_mercado_livre_explica(self):
        MarketplaceAccount.objects.all().delete()
        d = self.rascunho(fotos=[self.foto()])
        with mercado_livre_falso(), self.assertRaisesMessage(Exception, "Conecte uma conta do Mercado Livre"):
            anuncio.diagnosticar(d)


class ApiTests(Base):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user("anunciante")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def permitir(self, *codenames):
        self.user.user_permissions.set(Permission.objects.filter(codename__in=codenames))
        self.user = get_user_model().objects.get(pk=self.user.pk)
        self.client.force_authenticate(self.user)

    def test_validar_exige_permissao_de_alterar(self):
        d = self.rascunho(fotos=[self.foto()])
        self.permitir("view_listingdraft")
        with mercado_livre_falso():
            self.assertEqual(self.client.post(f"/api/v1/listing-drafts/{d.id}/validate/").status_code, 403)
        self.permitir("view_listingdraft", "change_listingdraft")
        with mercado_livre_falso():
            r = self.client.post(f"/api/v1/listing-drafts/{d.id}/validate/")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["pode_publicar"])

    def test_sugestao_de_categoria_e_atributos(self):
        self.permitir("view_listingdraft")
        with mercado_livre_falso():
            r = self.client.get("/api/v1/listing-drafts/ml-categories/?q=luminaria pimentao")
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json()[0]["category_id"], "MLB1234")
            r = self.client.get("/api/v1/listing-drafts/ml-attributes/?category_id=MLB1234")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["category"]["max_pictures_per_item"], 3)
        self.assertNotIn("GTIN", [a["id"] for a in r.json()["attributes"]])

    def test_arvore_de_categorias_navega_ate_a_folha(self):
        self.permitir("view_listingdraft")
        with mercado_livre_falso():
            raiz = self.client.get("/api/v1/listing-drafts/ml-category-tree/").json()
            meio = self.client.get("/api/v1/listing-drafts/ml-category-tree/?category_id=MLB1574").json()
            folha = self.client.get("/api/v1/listing-drafts/ml-category-tree/?category_id=MLB1234").json()
        self.assertEqual([c["name"] for c in raiz["children"]], ["Casa", "Brinquedos"])
        self.assertFalse(raiz["listing_allowed"])
        # categoria com filhas não recebe anúncio, mesmo que o settings diga que sim
        self.assertEqual(meio["children"], [{"id": "MLB1234", "name": "Luminárias"}])
        self.assertFalse(meio["listing_allowed"])
        self.assertEqual(folha["children"], [])
        self.assertTrue(folha["listing_allowed"])
        self.assertEqual(self.client.get(
            "/api/v1/listing-drafts/ml-category-tree/?category_id=../x"
        ).status_code, 400)

    def test_busca_curta_e_categoria_invalida_sao_recusadas(self):
        self.permitir("view_listingdraft")
        with mercado_livre_falso() as falso:
            self.assertEqual(self.client.get("/api/v1/listing-drafts/ml-categories/?q=ab").status_code, 400)
            self.assertEqual(
                self.client.get("/api/v1/listing-drafts/ml-attributes/?category_id=../../x").status_code, 400
            )
        self.assertEqual(falso.chamadas, [])

    def test_sem_conta_vira_400_legivel(self):
        MarketplaceAccount.objects.all().delete()
        self.permitir("view_listingdraft")
        with mercado_livre_falso():
            r = self.client.get("/api/v1/listing-drafts/ml-categories/?q=luminaria")
        self.assertEqual(r.status_code, 400)
        self.assertIn("Conecte uma conta", str(r.json()))


class ClienteValidateTests(TestCase):
    """O cliente real do Mercado Livre, com o transporte HTTP trocado por respostas gravadas."""

    def adaptador(self, status, body):
        from apps.integrations.meli.cliente import HttpResponse, MercadoLivreAdapter

        self.pedidos = []

        def transporte(method, path, *, token="", data=None, form=False, headers=None):
            self.pedidos.append((method, path))
            return HttpResponse(status, body, {})

        return MercadoLivreAdapter(transporte=transporte, config={
            "client_id": "1", "client_secret": "s", "redirect_uri": "https://x/cb",
        })

    def conta(self):
        return MarketplaceAccount(channel="mercado_livre", external_id="96417426", access_token="tok")

    def test_204_e_anuncio_aceito(self):
        a = self.adaptador(204, {})
        self.assertEqual(a.validate_item(account=self.conta(), payload={"title": "x"}), [])
        self.assertEqual(self.pedidos, [("POST", "/items/validate")])

    def test_400_devolve_as_causas_sem_levantar_erro(self):
        causas = [{"type": "error", "code": "item.price.invalid", "message": "min price"}]
        a = self.adaptador(400, {"message": "Validation error", "cause": causas})
        self.assertEqual(a.validate_item(account=self.conta(), payload={}), causas)

    def test_400_sem_causa_vira_erro_de_formato(self):
        a = self.adaptador(400, {"message": "body.invalid_field_types", "error": "price expected Number"})
        r = a.validate_item(account=self.conta(), payload={})
        self.assertEqual(r[0]["type"], "error")
        self.assertIn("price expected Number", r[0]["message"])

    def test_401_pede_renovar_token(self):
        from apps.integrations.base import IntegrationError

        a = self.adaptador(401, {})
        with self.assertRaises(IntegrationError) as ctx:
            a.validate_item(account=self.conta(), payload={})
        self.assertTrue(ctx.exception.token_invalido)

    def test_sugestao_monta_a_busca_do_site_brasileiro(self):
        a = self.adaptador(200, [{"category_id": "MLB1"}])
        a.suggest_categories(account=self.conta(), q="luminária pimentão", limit=3)
        metodo, caminho = self.pedidos[0]
        self.assertEqual(metodo, "GET")
        self.assertTrue(caminho.startswith("/sites/MLB/domain_discovery/search?"))
        self.assertIn("limit=3", caminho)
