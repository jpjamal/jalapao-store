"""Ordem de envio Shopee sob duas solicitações simultâneas no PostgreSQL."""

from contextlib import contextmanager
from datetime import timedelta
from threading import Event, Lock, Thread
from unittest import skipUnless

from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase
from django.utils import timezone

from apps.catalog.models import Product
from apps.integrations import base, services
from apps.integrations.models import Listing, MarketplaceAccount, OutboxEvent
from apps.inventory.models import Stock


@skipUnless(connection.vendor == "postgresql", "Bloqueio de linha exige PostgreSQL")
class StockOrderingTests(TransactionTestCase):
    def test_segunda_chamada_le_saldo_depois_da_primeira(self):
        conta = MarketplaceAccount.objects.create(
            channel="shopee", external_id="77", access_token="tok",
            token_expires_at=timezone.now() + timedelta(hours=2),
        )
        produto = Product.objects.create(sku="P", name="Peça")
        saldo = Stock.objects.create(product=produto, quantity=7, version=1)
        vinculo = Listing.objects.create(
            product=produto, marketplace="shopee", seller_id="77",
            item_id="item", sync_enabled=True,
        )
        OutboxEvent.objects.create(topic=services.TOPICO_ESTOQUE, payload={
            "product_id": str(produto.pk), "quantity": 7, "version": 1,
        })

        entrou = Event()
        liberar = Event()
        chamadas = []
        erros = []
        trava = Lock()

        class Falso:
            channel = "shopee"

            def update_stock(self, *, account, item_id, quantity):
                with trava:
                    chamadas.append(quantity)
                    primeira = len(chamadas) == 1
                if primeira:
                    entrou.set()
                    if not liberar.wait(10):
                        raise TimeoutError("Primeiro envio não foi liberado")

        @contextmanager
        def usando():
            anterior = base._ADAPTADORES["shopee"]
            base._ADAPTADORES["shopee"] = Falso
            try:
                yield
            finally:
                base._ADAPTADORES["shopee"] = anterior

        def enviar():
            try:
                close_old_connections()
                services.enviar_estoque(MarketplaceAccount.objects.get(pk=conta.pk))
            except Exception as exc:
                erros.append(exc)
            finally:
                connections.close_all()

        primeiro = Thread(target=enviar)
        segundo = Thread(target=enviar)
        with usando():
            primeiro.start()
            try:
                self.assertTrue(entrou.wait(10))
                saldo.quantity = 3
                saldo.version = 2
                saldo.save(update_fields=["quantity", "version"])
                OutboxEvent.objects.create(topic=services.TOPICO_ESTOQUE, payload={
                    "product_id": str(produto.pk), "quantity": 3, "version": 2,
                })
                segundo.start()
            finally:
                liberar.set()
                primeiro.join(10)
                if segundo.ident is not None:
                    segundo.join(10)

        self.assertFalse(primeiro.is_alive())
        self.assertFalse(segundo.is_alive())
        self.assertEqual(erros, [])
        self.assertEqual(chamadas, [7, 3])
        vinculo.refresh_from_db()
        self.assertEqual(vinculo.last_pushed_version, 2)
