"""Spec 012 — publicar o rascunho no Mercado Livre.

O adaptador é de mentira: cada teste diz o que o Mercado Livre responderia e confere o que
o sistema mandou e o que gravou. Nenhum teste fala com a rede.
"""

import shutil
import tempfile
from contextlib import contextmanager

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from apps.catalog.models import ProductImage
from apps.integrations import base
from apps.integrations.base import IntegrationError
from apps.integrations.meli.publicacao import publicar
from apps.integrations.models import Listing
from apps.inventory.models import Stock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from rest_framework.test import APIClient

from .test_validacao_anuncio import Base, Falso

MIDIA = tempfile.mkdtemp(prefix="jalapao-teste-")


class Publicador(Falso):
    """O Falso da validação, mais as três chamadas que criam algo. O registro das chamadas
    fica nos atributos do Falso, que é onde os métodos herdados escrevem."""

    criar = []          # respostas de create_item, em ordem: (item, causas)
    descricao_falha = False

    def upload_picture(self, *, account, filename, content, mime_type):
        Falso.chamadas.append(("upload_picture", filename))
        return f"FOTO-{len([c for c in Falso.chamadas if c[0] == 'upload_picture'])}"

    def create_item(self, *, account, payload):
        Falso.chamadas.append(("create_item", payload.get("title")))
        Falso.ultimo_envio = payload
        return Publicador.criar.pop(0)

    def set_description(self, *, account, item_id, text):
        Falso.chamadas.append(("set_description", item_id))
        if Publicador.descricao_falha:
            raise IntegrationError("Mercado Livre respondeu HTTP 500.")


ITEM = {
    "id": "MLB5000", "seller_id": 96417426, "title": "Luminária Pimentão 3D",
    "status": "active", "permalink": "https://produto.mercadolivre.com.br/MLB-5000",
    "user_product_id": "MLBU77", "family_id": "F1", "available_quantity": 5,
}


@contextmanager
def mercado_livre_publicando(criar=None, causas=(), descricao_falha=False):
    original = base._ADAPTADORES.get("mercado_livre")
    Falso.chamadas, Falso.causas, Falso.ultimo_envio = [], list(causas), None
    Publicador.criar = list(criar if criar is not None else [(dict(ITEM), [])])
    Publicador.descricao_falha = descricao_falha
    base._ADAPTADORES["mercado_livre"] = Publicador
    try:
        yield Falso
    finally:
        base._ADAPTADORES["mercado_livre"] = original


@override_settings(MEDIA_ROOT=MIDIA)
class PublicacaoTests(Base):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MIDIA, ignore_errors=True)

    def foto(self, mime="image/jpeg", w=1200, h=1200):
        return ProductImage.objects.create(
            product=self.produto, file=SimpleUploadedFile("x.jpg", b"\xff\xd8\xffjpeg"),
            mime_type=mime, width=w, height=h, size_bytes=8,
        )

    def test_publica_com_fotos_estoque_real_e_descricao(self):
        d = self.rascunho(fotos=[self.foto(), self.foto()])
        with mercado_livre_publicando() as ml:
            r = publicar(d.pk)
        operacoes = [nome for nome, _ in ml.chamadas]
        # valida antes, sobe as fotos, cria e só então a descrição
        self.assertLess(operacoes.index("validate_item"), operacoes.index("upload_picture"))
        self.assertLess(operacoes.index("upload_picture"), operacoes.index("create_item"))
        self.assertEqual(operacoes[-1], "set_description")
        self.assertEqual(ml.ultimo_envio["pictures"], [{"id": "FOTO-1"}, {"id": "FOTO-2"}])
        self.assertEqual(ml.ultimo_envio["available_quantity"], 5)
        self.assertNotIn("12.34", str(ml.ultimo_envio))  # custo nunca sai
        self.assertEqual(r["item_id"], "MLB5000")
        self.assertEqual(r["fotos"], 2)
        listing = Listing.objects.get()
        self.assertEqual(listing.draft, d)
        self.assertEqual((listing.item_id, listing.user_product_id), ("MLB5000", "MLBU77"))
        self.assertFalse(listing.sync_enabled)  # sincronizar estoque continua sendo escolha do dono

    def test_nunca_publica_duas_vezes(self):
        d = self.rascunho(fotos=[self.foto()])
        with mercado_livre_publicando():
            publicar(d.pk)
        with mercado_livre_publicando() as ml, self.assertRaisesMessage(IntegrationError, "já foi publicado"):
            publicar(d.pk)
        self.assertEqual(ml.chamadas, [])
        self.assertEqual(Listing.objects.count(), 1)

    def test_sem_estoque_nao_chama_o_mercado_livre(self):
        Stock.objects.filter(product=self.produto).update(quantity=0, value=0)
        d = self.rascunho(fotos=[self.foto()])
        with mercado_livre_publicando() as ml, self.assertRaisesMessage(IntegrationError, "sem estoque"):
            publicar(d.pk)
        self.assertEqual(ml.chamadas, [])

    def test_rascunho_invalido_para_antes_das_fotos(self):
        d = self.rascunho(fotos=[self.foto()])
        causa = {"type": "error", "code": "item.attributes.missing_required", "message": "Falta COLOR"}
        with mercado_livre_publicando(causas=[causa]) as ml, self.assertRaisesMessage(IntegrationError, "Falta COLOR"):
            publicar(d.pk)
        self.assertNotIn("upload_picture", [n for n, _ in ml.chamadas])
        self.assertNotIn("create_item", [n for n, _ in ml.chamadas])

    def test_recusa_na_criacao_nao_grava_vinculo(self):
        d = self.rascunho(fotos=[self.foto()])
        recusa = (None, [{"type": "error", "code": "item.price.invalid", "message": "Preço inválido"}])
        with mercado_livre_publicando(criar=[recusa]), self.assertRaisesMessage(IntegrationError, "Preço inválido"):
            publicar(d.pk)
        self.assertEqual(Listing.objects.count(), 0)

    def test_criacao_se_ajusta_a_produto_do_vendedor(self):
        d = self.rascunho(fotos=[self.foto()])
        pede = (None, [{"type": "error", "code": "body.required_fields", "references": ["family_name"],
                        "message": ""}])
        with mercado_livre_publicando(criar=[pede, (dict(ITEM), [])]) as ml:
            publicar(d.pk)
        self.assertEqual(ml.ultimo_envio["family_name"], "Luminária Pimentão 3D")

    def test_falha_na_descricao_vira_aviso_e_mantem_o_anuncio(self):
        d = self.rascunho(fotos=[self.foto()])
        with mercado_livre_publicando(descricao_falha=True):
            r = publicar(d.pk)
        self.assertIn("descrição não foi gravada", r["avisos"][0])
        self.assertEqual(Listing.objects.count(), 1)


@override_settings(MEDIA_ROOT=MIDIA)
class PublicacaoApiTests(Base):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user("publicador")
        self.client = APIClient()
        self.permitir()

    def permitir(self, *codenames):
        self.user.user_permissions.set(Permission.objects.filter(codename__in=codenames))
        self.user = get_user_model().objects.get(pk=self.user.pk)
        self.client.force_authenticate(self.user)

    def test_publicar_exige_permissao_propria(self):
        foto = ProductImage.objects.create(
            product=self.produto, file=SimpleUploadedFile("x.jpg", b"\xff\xd8\xffjpeg"),
            mime_type="image/jpeg", width=1200, height=1200, size_bytes=8,
        )
        d = self.rascunho(fotos=[foto])
        url = f"/api/v1/listing-drafts/{d.id}/publish/"
        self.permitir("view_listingdraft", "change_listingdraft")
        with mercado_livre_publicando() as ml:
            self.assertEqual(self.client.post(url).status_code, 403)
        self.assertEqual(ml.chamadas, [])
        self.permitir("view_listingdraft", "change_listingdraft", "publish_listingdraft")
        with mercado_livre_publicando():
            r = self.client.post(url)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["item_id"], "MLB5000")
        self.assertEqual(self.client.get(f"/api/v1/listing-drafts/{d.id}/").json()["published_item_id"], "MLB5000")
        with mercado_livre_publicando():
            r = self.client.post(url)
        self.assertEqual(r.status_code, 400)
        self.assertIn("já foi publicado", str(r.json()))


class ClientePublicacaoTests(Base):
    """O cliente real, com o transporte HTTP trocado por respostas gravadas."""

    def adaptador(self, *respostas):
        from apps.integrations.meli.cliente import HttpResponse, MercadoLivreAdapter

        self.pedidos = []
        fila = list(respostas)

        def transporte(method, path, **kwargs):
            self.pedidos.append((method, path, kwargs))
            status, body = fila.pop(0)
            return HttpResponse(status, body, {})

        return MercadoLivreAdapter(transporte=transporte, config={
            "client_id": "1", "client_secret": "s", "redirect_uri": "https://x/cb",
        })

    def conta(self):
        from apps.integrations.models import MarketplaceAccount

        return MarketplaceAccount.objects.get()

    def test_foto_vai_em_multipart_e_devolve_o_id(self):
        adap = self.adaptador((201, {"id": "123-MLB456_092026"}))
        foto_id = adap.upload_picture(
            account=self.conta(), filename='a"b.jpg', content=b"\xff\xd8bytes", mime_type="image/jpeg"
        )
        self.assertEqual(foto_id, "123-MLB456_092026")
        method, path, kw = self.pedidos[0]
        self.assertEqual((method, path), ("POST", "/pictures/items/upload"))
        self.assertTrue(kw["headers"]["Content-Type"].startswith("multipart/form-data; boundary="))
        self.assertIn(b'name="file"; filename="ab.jpg"', kw["raw"])
        self.assertIn(b"\xff\xd8bytes", kw["raw"])

    def test_criacao_devolve_item_ou_causas(self):
        adap = self.adaptador(
            (201, {"id": "MLB1"}),
            (400, {"cause": [{"type": "error", "code": "x", "message": "m"}]}),
            (400, {"error": "validation_error", "message": "body invalid"}),
        )
        self.assertEqual(adap.create_item(account=self.conta(), payload={}), ({"id": "MLB1"}, []))
        self.assertEqual(adap.create_item(account=self.conta(), payload={})[1][0]["message"], "m")
        self.assertEqual(adap.create_item(account=self.conta(), payload={})[1][0]["message"], "body invalid")

    def test_descricao_vai_em_texto_simples(self):
        adap = self.adaptador((201, {}))
        adap.set_description(account=self.conta(), item_id="MLB1", text="Peça 3D")
        method, path, kw = self.pedidos[0]
        self.assertEqual((method, path, kw["data"]), ("POST", "/items/MLB1/description", {"plain_text": "Peça 3D"}))
