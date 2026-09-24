"""Segredos persistidos e conversão da base anterior à criptografia."""

from importlib import import_module
from types import SimpleNamespace

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, override_settings

from apps.integrations.fields import PREFIXO, TokenDecryptionError
from apps.integrations.models import MarketplaceAccount
from apps.integrations.models import OAuthAttempt
from django.contrib.auth import get_user_model
from django.utils import timezone


class EncryptedFieldTests(TestCase):
    def test_tokens_sao_cifrados_no_banco_e_lidos_em_memoria(self):
        conta = MarketplaceAccount.objects.create(
            channel="shopee", external_id="1",
            access_token="acesso-sensivel", refresh_token="refresh-sensivel",
        )
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT access_token, refresh_token FROM integrations_marketplaceaccount WHERE id = %s",
                [conta.pk.hex if connection.vendor == "sqlite" else str(conta.pk)],
            )
            acesso, refresh = cursor.fetchone()
        self.assertTrue(acesso.startswith(PREFIXO))
        self.assertTrue(refresh.startswith(PREFIXO))
        self.assertNotIn("acesso-sensivel", acesso)
        self.assertNotIn("refresh-sensivel", refresh)
        conta.refresh_from_db()
        self.assertEqual(conta.access_token, "acesso-sensivel")
        self.assertEqual(conta.refresh_token, "refresh-sensivel")

    def test_chave_errada_falha_sem_expor_token(self):
        MarketplaceAccount.objects.create(
            channel="mercado_livre", external_id="2", access_token="segredo",
        )
        with override_settings(SECRET_KEY="outra-chave-independente-suficientemente-longa"):
            with self.assertRaises(TokenDecryptionError) as context:
                MarketplaceAccount.objects.get(external_id="2")
        self.assertNotIn("segredo", str(context.exception))

    def test_verificador_pkce_tambem_fica_cifrado(self):
        user = get_user_model().objects.create_user("pkce")
        attempt = OAuthAttempt.objects.create(
            user=user, state_hash="a" * 64, code_verifier="verificador-sensivel",
            expires_at=timezone.now(),
        )
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT code_verifier FROM integrations_oauthattempt WHERE id = %s",
                [attempt.pk.hex if connection.vendor == "sqlite" else str(attempt.pk)],
            )
            stored = cursor.fetchone()[0]
        self.assertTrue(stored.startswith(PREFIXO))
        self.assertNotIn("verificador-sensivel", stored)
        attempt.refresh_from_db()
        self.assertEqual(attempt.code_verifier, "verificador-sensivel")


class LegacyTokenMigrationTests(TestCase):
    def test_migracao_preserva_e_cifra_tokens_antigos(self):
        executor = MigrationExecutor(connection)
        anterior = [("integrations", "0003_oauthattempt")]
        old_apps = executor.loader.project_state(anterior).apps
        OldAccount = old_apps.get_model("integrations", "MarketplaceAccount")
        conta = OldAccount.objects.create(
            channel="shopee", external_id="legacy",
            access_token="acesso-antigo", refresh_token="refresh-antigo",
        )
        migration = import_module("apps.integrations.migrations.0004_proteger_tokens_e_versao_envio")
        migration.cifrar_legado(old_apps, SimpleNamespace(connection=connection))
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT access_token, refresh_token FROM integrations_marketplaceaccount WHERE id = %s",
                [conta.pk.hex if connection.vendor == "sqlite" else str(conta.pk)],
            )
            acesso, refresh = cursor.fetchone()
        self.assertTrue(acesso.startswith(PREFIXO))
        self.assertTrue(refresh.startswith(PREFIXO))
        novo = MarketplaceAccount.objects.get(pk=conta.pk)
        self.assertEqual(novo.access_token, "acesso-antigo")
        self.assertEqual(novo.refresh_token, "refresh-antigo")
