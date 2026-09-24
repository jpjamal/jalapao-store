"""Integração com marketplace, provada sem rede e sem credencial de verdade.

O transporte do cliente é injetável justamente para isto: o que dá para provar daqui é a
nossa metade — assinatura, ciclo de token, casamento por SKU, o interruptor de sincronia e
o comportamento diante de erro. O que depende do servidor da Shopee responder fica anotado
como não verificado na validação da spec 005.
"""

import hashlib
import hmac
import json
import os
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.catalog.models import Product
from apps.inventory.models import Stock
from apps.integrations import services
from apps.integrations.base import IntegrationError, adaptador
from apps.integrations.models import Listing, MarketplaceAccount, OutboxEvent
from apps.integrations.shopee.assinatura import assinar, base_string
from apps.integrations.shopee.cliente import ShopeeAdapter

CONFIG = {
    "partner_id": "1000001",
    "partner_key": "chave-de-teste",
    "redirect_uri": "https://217.216.82.25/jalapao-store/callback",
    "base": "https://exemplo.invalido",
}


class Gravador:
    """Transporte falso: devolve respostas na ordem e guarda o que foi chamado."""

    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.chamadas = []

    def __call__(self, metodo, url, corpo=None, timeout=20):
        self.chamadas.append({"metodo": metodo, "url": url, "corpo": corpo})
        return self.respostas.pop(0) if self.respostas else {}


def adaptador_falso(respostas):
    return ShopeeAdapter(transporte=Gravador(respostas), config=CONFIG)


class AssinaturaTests(TestCase):
    def test_ordem_da_base_string(self):
        # pública: partner_id + caminho + timestamp
        self.assertEqual(
            base_string(partner_id="123", caminho="/api/v2/auth/token/get", timestamp=1610000000),
            "123/api/v2/auth/token/get1610000000",
        )
        # de loja: + access_token + shop_id, nesta ordem
        self.assertEqual(
            base_string(
                partner_id="123",
                caminho="/api/v2/product/get_item_list",
                timestamp=1610000000,
                access_token="tok",
                shop_id="777",
            ),
            "123/api/v2/product/get_item_list1610000000tok777",
        )

    def test_hmac_sha256_em_hexadecimal(self):
        esperado = hmac.new(
            b"chave-de-teste", b"1000001/api/v2/shop/get_shop_info1610000000tok777", hashlib.sha256
        ).hexdigest()
        self.assertEqual(
            assinar(
                partner_key="chave-de-teste",
                partner_id="1000001",
                caminho="/api/v2/shop/get_shop_info",
                timestamp=1610000000,
                access_token="tok",
                shop_id="777",
            ),
            esperado,
        )
        self.assertEqual(len(esperado), 64)

    def test_assinatura_muda_com_qualquer_campo(self):
        base = dict(
            partner_key="k", partner_id="1", caminho="/a", timestamp=1, access_token="t", shop_id="9"
        )
        sozinha = assinar(**base)
        for campo, valor in [
            ("partner_id", "2"),
            ("caminho", "/b"),
            ("timestamp", 2),
            ("access_token", "u"),
            ("shop_id", "8"),
            ("partner_key", "j"),
        ]:
            self.assertNotEqual(sozinha, assinar(**{**base, campo: valor}), campo)


class LinkDeAutorizacaoTests(TestCase):
    def test_link_leva_assinatura_e_o_redirect_configurado(self):
        url = adaptador_falso([]).authorization_url()
        self.assertTrue(url.startswith("https://exemplo.invalido/api/v2/shop/auth_partner?"))
        self.assertIn("partner_id=1000001", url)
        self.assertIn("sign=", url)
        # o IP vai como redirect; se a Shopee recusar, muda a variável e não o código
        self.assertIn("217.216.82.25", url)

    def test_sem_credenciais_o_erro_diz_o_que_configurar(self):
        with patch.dict(os.environ, {"SHOPEE_PARTNER_ID": "", "SHOPEE_PARTNER_KEY": ""}):
            vazio = ShopeeAdapter(transporte=Gravador([]), config={"partner_id": "", "partner_key": ""})
            with self.assertRaises(IntegrationError) as ctx:
                vazio.authorization_url()
        self.assertIn("SHOPEE_PARTNER_ID", str(ctx.exception))


class TokenTests(TestCase):
    def setUp(self):
        self.conta = MarketplaceAccount.objects.create(
            channel="shopee", external_id="777", access_token="velho", refresh_token="refresh-1"
        )

    def test_conectar_guarda_tokens_e_prazo_da_autorizacao(self):
        adap = adaptador_falso(
            [{"access_token": "novo", "refresh_token": "refresh-2", "expire_in": 14400}]
        )
        with self._usando(adap):
            conta = services.conectar(canal="shopee", code="abc", external_id="777")
        self.assertEqual(conta.access_token, "novo")
        self.assertEqual(conta.refresh_token, "refresh-2")
        self.assertTrue(conta.token_valido)
        # a Shopee não devolve a validade da autorização: assumimos o teto de 365 dias
        self.assertIsNotNone(conta.authorization_expires_at)
        self.assertGreater(conta.dias_ate_expirar_autorizacao, 360)

    def test_token_perto_de_vencer_e_renovado_antes_da_chamada(self):
        self.conta.token_expires_at = timezone.now() + timedelta(minutes=2)
        self.conta.save()
        gravador = Gravador(
            [
                {"access_token": "renovado", "refresh_token": "refresh-2", "expire_in": 14400},
                {"response": {"shop_name": "Jalapão"}},
            ]
        )
        adap = ShopeeAdapter(transporte=gravador, config=CONFIG)
        with self._usando(adap):
            services.chamar(self.conta, "shop_info")
        self.conta.refresh_from_db()
        self.assertEqual(self.conta.access_token, "renovado")
        self.assertEqual(len(gravador.chamadas), 2)

    def test_token_recusado_renova_e_tenta_uma_vez_so(self):
        self.conta.token_expires_at = timezone.now() + timedelta(hours=3)
        self.conta.save()
        gravador = Gravador(
            [
                {"error": "error_auth", "message": "invalid token"},
                {"access_token": "renovado", "refresh_token": "r", "expire_in": 14400},
                {"response": {"shop_name": "Jalapão"}},
            ]
        )
        adap = ShopeeAdapter(transporte=gravador, config=CONFIG)
        with self._usando(adap):
            resposta = services.chamar(self.conta, "shop_info")
        self.assertEqual(resposta["response"]["shop_name"], "Jalapão")
        self.assertEqual(len(gravador.chamadas), 3)

    def test_erro_que_nao_e_de_token_nao_vira_laco(self):
        self.conta.token_expires_at = timezone.now() + timedelta(hours=3)
        self.conta.save()
        gravador = Gravador([{"error": "error_param", "message": "item_id inválido"}])
        adap = ShopeeAdapter(transporte=gravador, config=CONFIG)
        with self._usando(adap), self.assertRaises(IntegrationError) as ctx:
            services.chamar(self.conta, "shop_info")
        self.assertIn("item_id inválido", str(ctx.exception))
        self.assertEqual(len(gravador.chamadas), 1)

    def _usando(self, adap):
        """Troca o adaptador registrado pelo de teste enquanto o bloco roda."""
        from contextlib import contextmanager

        from apps.integrations import base

        @contextmanager
        def trocar():
            original = base._ADAPTADORES["shopee"]
            base._ADAPTADORES["shopee"] = lambda: adap
            try:
                yield
            finally:
                base._ADAPTADORES["shopee"] = original

        return trocar()


class CatalogoTests(TestCase):
    def setUp(self):
        self.conta = MarketplaceAccount.objects.create(
            channel="shopee",
            external_id="777",
            access_token="tok",
            token_expires_at=timezone.now() + timedelta(hours=3),
        )
        self.produto = Product.objects.create(sku="3D-ZE-PILINTRA", name="Ze pilintra 15cm")

    def _com_itens(self, itens):
        from contextlib import contextmanager

        from apps.integrations import base
        from apps.integrations.base import RemoteItem

        class Falso:
            channel = "shopee"

            def list_items(self, *, account):
                return [RemoteItem(**i) for i in itens]

        @contextmanager
        def trocar():
            original = base._ADAPTADORES["shopee"]
            base._ADAPTADORES["shopee"] = Falso
            try:
                yield
            finally:
                base._ADAPTADORES["shopee"] = original

        return trocar()

    def test_casa_por_sku_ignorando_caixa_e_espaco(self):
        with self._com_itens(
            [{"item_id": "111", "title": "Zé Pilintra", "sku": " 3d-ze-pilintra ", "stock": 4}]
        ):
            resultado = services.importar_anuncios(self.conta)
        vinculo = Listing.objects.get(item_id="111")
        self.assertEqual(vinculo.product, self.produto)
        self.assertEqual(vinculo.remote_stock, 4)
        self.assertEqual(resultado["vinculos_novos"], 1)
        self.assertEqual(resultado["pendentes"], [])

    def test_anuncio_sem_correspondencia_fica_pendente_e_nao_cria_produto(self):
        antes = Product.objects.count()
        with self._com_itens([{"item_id": "222", "title": "Camiseta", "sku": "NAO-EXISTE"}]):
            resultado = services.importar_anuncios(self.conta)
        self.assertEqual(Product.objects.count(), antes)
        self.assertFalse(Listing.objects.filter(item_id="222").exists())
        self.assertEqual(len(resultado["pendentes"]), 1)
        self.assertEqual(resultado["pendentes"][0]["item_id"], "222")

    def test_reimportar_atualiza_o_vinculo_sem_duplicar(self):
        with self._com_itens([{"item_id": "111", "title": "A", "sku": "3D-ZE-PILINTRA", "stock": 1}]):
            services.importar_anuncios(self.conta)
        with self._com_itens([{"item_id": "111", "title": "B", "sku": "3D-ZE-PILINTRA", "stock": 9}]):
            services.importar_anuncios(self.conta)
        self.assertEqual(Listing.objects.filter(item_id="111").count(), 1)
        vinculo = Listing.objects.get(item_id="111")
        self.assertEqual(vinculo.title, "B")
        self.assertEqual(vinculo.remote_stock, 9)

    def test_importar_nao_mexe_em_estoque_local(self):
        with self._com_itens(
            [{"item_id": "111", "title": "A", "sku": "3D-ZE-PILINTRA", "stock": 50}]
        ):
            services.importar_anuncios(self.conta)
        self.produto.refresh_from_db()
        self.assertFalse(hasattr(self.produto, "stock") and self.produto.stock.quantity)


class EstoqueTests(TestCase):
    def setUp(self):
        self.conta = MarketplaceAccount.objects.create(
            channel="shopee",
            external_id="777",
            access_token="tok",
            token_expires_at=timezone.now() + timedelta(hours=3),
        )
        self.produto = Product.objects.create(sku="SKU-1", name="Peça")
        Stock.objects.create(product=self.produto, quantity=7, version=1)
        self.vinculo = Listing.objects.create(
            product=self.produto,
            marketplace="shopee",
            seller_id="777",
            item_id="111",
            sync_enabled=False,
        )
        self.enviados = []

    def _com_envio(self, erro=None):
        from contextlib import contextmanager

        from apps.integrations import base

        registro = self.enviados

        class Falso:
            channel = "shopee"

            def update_stock(self, *, account, item_id, quantity):
                if erro:
                    raise IntegrationError(erro)
                registro.append((item_id, quantity))

        @contextmanager
        def trocar():
            original = base._ADAPTADORES["shopee"]
            base._ADAPTADORES["shopee"] = Falso
            try:
                yield
            finally:
                base._ADAPTADORES["shopee"] = original

        return trocar()

    def _evento(self, quantidade=7):
        return OutboxEvent.objects.create(
            topic=services.TOPICO_ESTOQUE,
            payload={"product_id": str(self.produto.id), "quantity": quantidade, "version": 1},
        )

    def test_interruptor_desligado_nao_envia_e_encerra_o_evento(self):
        evento = self._evento()
        with self._com_envio():
            resultado = services.enviar_estoque(self.conta)
        self.assertEqual(self.enviados, [])
        self.assertEqual(resultado["ignorados"], 1)
        evento.refresh_from_db()
        self.assertIsNotNone(evento.delivered_at)  # fila que não anda vira fila infinita

    def test_interruptor_ligado_leva_o_saldo(self):
        self.vinculo.sync_enabled = True
        self.vinculo.save()
        evento = self._evento(quantidade=7)
        with self._com_envio():
            resultado = services.enviar_estoque(self.conta)
        self.assertEqual(self.enviados, [("111", 7)])
        self.assertEqual(resultado["enviados"], 1)
        evento.refresh_from_db()
        self.assertIsNotNone(evento.delivered_at)
        self.vinculo.refresh_from_db()
        self.assertEqual(self.vinculo.remote_stock, 7)
        self.assertIsNotNone(self.vinculo.stock_pushed_at)

    def test_falha_no_envio_guarda_o_erro_e_nao_encerra_o_evento(self):
        self.vinculo.sync_enabled = True
        self.vinculo.save()
        evento = self._evento()
        with self._com_envio(erro="Shopee fora do ar"):
            resultado = services.enviar_estoque(self.conta)
        self.assertEqual(resultado["enviados"], 0)
        self.assertEqual(len(resultado["falhas"]), 1)
        evento.refresh_from_db()
        self.assertIsNone(evento.delivered_at)  # continua pendente para a próxima tentativa
        self.assertEqual(evento.attempts, 1)
        self.assertIn("fora do ar", evento.last_error)

    def test_venda_grava_a_intencao_de_sincronizar(self):
        """O outbox já existia no ajuste de estoque; a integração só passou a consumi-lo."""
        from apps.inventory.services import adjust_stock

        user = get_user_model().objects.create_user("operador")
        adjust_stock(
            product_id=self.produto.id, delta=3, reason="Entrada", actor=user, unit_cost=10
        )
        self.assertTrue(
            OutboxEvent.objects.filter(
                topic=services.TOPICO_ESTOQUE, delivered_at__isnull=True
            ).exists()
        )

    def test_duas_contas_precisam_receber_antes_do_evento_ser_encerrado(self):
        outra = MarketplaceAccount.objects.create(
            channel="shopee", external_id="888", access_token="tok",
            token_expires_at=timezone.now() + timedelta(hours=3),
        )
        Listing.objects.create(
            product=self.produto, marketplace="shopee", seller_id="888",
            item_id="222", sync_enabled=True,
        )
        self.vinculo.sync_enabled = True
        self.vinculo.save()
        evento = self._evento()
        with self._com_envio():
            services.enviar_estoque(self.conta)
            evento.refresh_from_db()
            self.assertIsNone(evento.delivered_at)
            services.enviar_estoque(outra)
        evento.refresh_from_db()
        self.assertIsNotNone(evento.delivered_at)
        self.assertEqual(self.enviados, [("111", 7), ("222", 7)])

    def test_repeticao_apos_falha_envia_saldo_mais_recente(self):
        self.vinculo.sync_enabled = True
        self.vinculo.save()
        antigo = self._evento(7)
        with self._com_envio(erro="indisponível"):
            services.enviar_estoque(self.conta)
        saldo = Stock.objects.get(product=self.produto)
        saldo.quantity = 3
        saldo.version = 2
        saldo.save(update_fields=["quantity", "version"])
        novo = OutboxEvent.objects.create(
            topic=services.TOPICO_ESTOQUE,
            payload={"product_id": str(self.produto.pk), "quantity": 3, "version": 2},
        )
        with self._com_envio():
            services.enviar_estoque(self.conta)
        self.assertEqual(self.enviados, [("111", 3)])
        self.vinculo.refresh_from_db()
        self.assertEqual(self.vinculo.last_pushed_version, 2)
        antigo.refresh_from_db()
        novo.refresh_from_db()
        self.assertIsNotNone(antigo.delivered_at)
        self.assertIsNotNone(novo.delivered_at)

    def test_ativar_vinculo_envia_estoque_mesmo_sem_evento(self):
        self.vinculo.sync_enabled = True
        self.vinculo.save()
        with self._com_envio():
            services.enviar_estoque(self.conta)
        self.assertEqual(self.enviados, [("111", 7)])

    def test_conta_desativada_nao_bloqueia_entrega_das_ativas(self):
        MarketplaceAccount.objects.create(
            channel="shopee", external_id="888", active=False,
        )
        Listing.objects.create(
            product=self.produto, marketplace="shopee", seller_id="888",
            item_id="222", sync_enabled=True,
        )
        self.vinculo.sync_enabled = True
        self.vinculo.save()
        evento = self._evento()
        with self._com_envio():
            services.enviar_estoque(self.conta)
        evento.refresh_from_db()
        self.assertIsNotNone(evento.delivered_at)
        self.assertEqual(self.enviados, [("111", 7)])


class ApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("dono")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.conta = MarketplaceAccount.objects.create(channel="shopee", external_id="777")

    def _permitir(self, *codenames):
        self.user.user_permissions.set(Permission.objects.filter(codename__in=codenames))
        self.user = get_user_model().objects.get(pk=self.user.pk)
        self.client.force_authenticate(self.user)

    def test_sem_permissao_nao_lista_nem_conecta(self):
        self.assertEqual(self.client.get("/api/v1/integrations/").status_code, 403)
        self.assertEqual(
            self.client.post("/api/v1/integrations/connect/", {}, format="json").status_code, 403
        )

    def test_leitura_nao_autoriza_conectar(self):
        self._permitir("view_marketplaceaccount")
        self.assertEqual(self.client.get("/api/v1/integrations/").status_code, 200)
        resposta = self.client.get("/api/v1/integrations/auth-link/?channel=shopee")
        self.assertEqual(resposta.status_code, 403)

    def test_connect_exige_code_e_loja(self):
        self._permitir("view_marketplaceaccount", "change_marketplaceaccount")
        resposta = self.client.post("/api/v1/integrations/connect/", {}, format="json")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("code", json.dumps(resposta.json()))

    def test_erro_de_integracao_vira_400_legivel(self):
        self._permitir("view_marketplaceaccount", "change_marketplaceaccount")
        resposta = self.client.get("/api/v1/integrations/auth-link/?channel=marte")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("marte", json.dumps(resposta.json()))

    def test_interruptor_do_vinculo_pelo_patch(self):
        produto = Product.objects.create(sku="S", name="P")
        vinculo = Listing.objects.create(
            product=produto, marketplace="shopee", seller_id="777", item_id="1",
            last_pushed_version=4,
        )
        self._permitir("view_listing", "change_listing")
        resposta = self.client.patch(
            f"/api/v1/listings/{vinculo.id}/", {"sync_enabled": True}, format="json"
        )
        self.assertEqual(resposta.status_code, 200)
        vinculo.refresh_from_db()
        self.assertTrue(vinculo.sync_enabled)
        self.assertIsNone(vinculo.last_pushed_version)


class RegistroTests(TestCase):
    def test_canal_desconhecido_avisa_em_vez_de_quebrar(self):
        with self.assertRaises(IntegrationError):
            adaptador("marte")

    def test_shopee_esta_registrada(self):
        self.assertEqual(adaptador("shopee").channel, "shopee")

    def test_o_registro_vem_do_ready_do_app_e_nao_do_import_do_teste(self):
        """Regressão: a tela respondia "canal sem integração" com os testes verdes.

        O decorador `@registrar` só roda quando alguém importa o pacote do canal. O teste
        importava direto e mascarava o fato de que, na aplicação rodando, ninguém importava.
        Quem garante isso é o `ready()` do AppConfig — é o que este teste prova, esvaziando
        o registro antes de chamá-lo.
        """
        import sys

        from django.apps import apps as django_apps

        from apps.integrations import base

        import apps.integrations as pacote

        original = dict(base._ADAPTADORES)
        # O decorador só roda no primeiro import. Para provar que é o ready() quem registra,
        # o módulo sai do cache — e o atributo sai do pacote pai junto, senão o
        # `from . import shopee` acha o atributo antigo e nem tenta importar de novo.
        modulos = [m for m in list(sys.modules) if m.startswith("apps.integrations.shopee")]
        guardados = {m: sys.modules.pop(m) for m in modulos}
        antigo = getattr(pacote, "shopee", None)
        if antigo is not None:
            delattr(pacote, "shopee")
        base._ADAPTADORES.clear()
        try:
            django_apps.get_app_config("integrations").ready()
            self.assertIn("shopee", base._ADAPTADORES)
        finally:
            base._ADAPTADORES.clear()
            base._ADAPTADORES.update(original)
            sys.modules.update(guardados)
            if antigo is not None:
                setattr(pacote, "shopee", antigo)


class AvisoDeAutorizacaoTests(TestCase):
    """A autorização vence calada: o token renova até o dia em que não renova mais."""

    def setUp(self):
        from apps.integrations.avisos import dias_de_alerta

        self.limiar = dias_de_alerta()

    def _conta(self, dias, **extra):
        return MarketplaceAccount.objects.create(
            channel="shopee",
            external_id=f"loja-{dias}",
            name=f"Loja {dias}",
            authorization_expires_at=timezone.now() + timedelta(days=dias, hours=1),
            **extra,
        )

    def test_longe_do_vencimento_nao_avisa(self):
        from apps.integrations.avisos import autorizacoes_a_vencer

        self._conta(self.limiar + 30)
        self.assertEqual(autorizacoes_a_vencer(), [])

    def test_dentro_do_limiar_avisa_com_os_dias_restantes(self):
        from apps.integrations.avisos import autorizacoes_a_vencer

        self._conta(self.limiar - 1)
        avisos = autorizacoes_a_vencer()
        self.assertEqual(len(avisos), 1)
        self.assertEqual(avisos[0]["days_left"], self.limiar - 1)
        self.assertEqual(avisos[0]["channel_label"], "Shopee")

    def test_ja_vencida_continua_aparecendo(self):
        from apps.integrations.avisos import autorizacoes_a_vencer

        self._conta(-3)
        avisos = autorizacoes_a_vencer()
        self.assertEqual(len(avisos), 1)
        self.assertLess(avisos[0]["days_left"], 0)

    def test_conta_desativada_e_sem_data_ficam_de_fora(self):
        from apps.integrations.avisos import autorizacoes_a_vencer

        self._conta(1, active=False)
        MarketplaceAccount.objects.create(
            channel="shopee", external_id="sem-data", authorization_expires_at=None
        )
        self.assertEqual(autorizacoes_a_vencer(), [])

    def test_o_painel_entrega_o_aviso(self):
        self._conta(2)
        user = get_user_model().objects.create_user("painel-integra")
        user.user_permissions.set(
            Permission.objects.filter(
                codename__in=["view_product", "view_sale", "view_cashentry"]
            )
        )
        client = APIClient()
        client.force_authenticate(user)
        corpo = client.get("/api/v1/dashboard/").json()
        self.assertEqual(len(corpo["authorization_alerts"]), 1)
        self.assertEqual(corpo["authorization_alerts"][0]["days_left"], 2)
