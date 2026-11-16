"""Esqueci minha senha (spec 039)."""

import re
from datetime import timedelta
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from apps.accounts.models import PasswordReset

SENHA_ANTIGA = "senha-antiga-12345"
SENHA_NOVA = "uma-senha-nova-forte-987"


def codigo_do_email(mensagem) -> str:
    achado = re.search(r"redefinir-senha/([0-9a-f]{64})", mensagem.body)
    assert achado, mensagem.body
    return achado.group(1)


class SenhaTests(TestCase):
    def setUp(self):
        cache.clear()  # o limite por IP usa o cache
        self.client = APIClient()
        self.usuario = get_user_model().objects.create_user(
            "jpmorais", email="dono@exemplo.com", password=SENHA_ANTIGA
        )

    def pedir(self, email="dono@exemplo.com"):
        return self.client.post("/api/v1/auth/forgot-password/", {"email": email}, format="json")

    def pedir_e_pegar_codigo(self) -> str:
        self.pedir()
        return codigo_do_email(mail.outbox[-1])

    def entrar(self, senha):
        return self.client.post(
            "/api/v1/auth/token/", {"username": "jpmorais", "password": senha}, format="json"
        )

    # --- recursos ---
    def test_resources_diz_se_o_email_esta_ligado(self):
        self.assertTrue(self.client.get("/api/v1/auth/resources/").json()["email_configured"])
        with override_settings(EMAIL_SEM_SMTP=False, EMAIL_HOST_USER="", EMAIL_HOST_PASSWORD=""):
            self.assertFalse(self.client.get("/api/v1/auth/resources/").json()["email_configured"])

    # --- pedido ---
    def test_conta_existente_recebe_o_link_e_a_resposta_e_a_mesma(self):
        existe = self.pedir()
        nao_existe = self.pedir("ninguem@exemplo.com")
        self.assertEqual(existe.status_code, 202)
        self.assertEqual(existe.json(), nao_existe.json())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["dono@exemplo.com"])
        self.assertIn("/jalapao-store/redefinir-senha/", mail.outbox[0].body)

    def test_banco_guarda_so_o_hash(self):
        codigo = self.pedir_e_pegar_codigo()
        pedido = PasswordReset.objects.get()
        self.assertNotEqual(pedido.code_hash, codigo)
        self.assertEqual(len(pedido.code_hash), 64)

    def test_email_sem_diferenca_de_maiuscula(self):
        self.pedir("DONO@Exemplo.com")
        self.assertEqual(len(mail.outbox), 1)

    def test_conta_inativa_nao_recebe(self):
        self.usuario.is_active = False
        self.usuario.save()
        self.assertEqual(self.pedir().status_code, 202)
        self.assertEqual(len(mail.outbox), 0)

    def test_quarto_pedido_na_mesma_hora_nao_envia(self):
        for _ in range(4):
            self.assertEqual(self.pedir().status_code, 202)
        self.assertEqual(len(mail.outbox), 3)

    def test_email_invalido_400(self):
        self.assertEqual(self.pedir("isso-nao-e-email").status_code, 400)

    def test_sem_email_configurado_nada_sai(self):
        with override_settings(EMAIL_SEM_SMTP=False, EMAIL_HOST_USER="", EMAIL_HOST_PASSWORD=""):
            self.assertEqual(self.pedir().status_code, 202)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(PasswordReset.objects.count(), 0)

    def test_falha_no_smtp_nao_quebra_a_resposta(self):
        with mock.patch("apps.common.email.send_mail", side_effect=OSError("sem rede")):
            self.assertEqual(self.pedir().status_code, 202)

    def test_limite_por_ip(self):
        respostas = [self.pedir(f"x{i}@exemplo.com").status_code for i in range(6)]
        self.assertEqual(respostas[:5], [202] * 5)
        self.assertEqual(respostas[5], 429)

    # --- link ---
    def test_link_valido_mostra_o_email_mascarado(self):
        codigo = self.pedir_e_pegar_codigo()
        resposta = self.client.get(f"/api/v1/auth/reset-password/{codigo}/")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["email"], "do***@exemplo.com")

    def test_link_inexistente_410(self):
        self.assertEqual(self.client.get("/api/v1/auth/reset-password/" + "a" * 64 + "/").status_code, 410)

    def test_link_vencido_410(self):
        codigo = self.pedir_e_pegar_codigo()
        PasswordReset.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.client.get(f"/api/v1/auth/reset-password/{codigo}/").status_code, 410)

    # --- troca ---
    def redefinir(self, codigo, senha=SENHA_NOVA, confirmacao=None):
        return self.client.post(
            f"/api/v1/auth/reset-password/{codigo}/",
            {"password": senha, "password_confirmation": senha if confirmacao is None else confirmacao},
            format="json",
        )

    def test_troca_a_senha_e_o_login_muda(self):
        codigo = self.pedir_e_pegar_codigo()
        self.assertEqual(self.redefinir(codigo).status_code, 200)
        self.assertEqual(self.entrar(SENHA_ANTIGA).status_code, 401)
        self.assertEqual(self.entrar(SENHA_NOVA).status_code, 200)

    def test_link_so_vale_uma_vez(self):
        codigo = self.pedir_e_pegar_codigo()
        self.assertEqual(self.redefinir(codigo).status_code, 200)
        self.assertEqual(self.redefinir(codigo, "outra-senha-forte-321").status_code, 410)
        self.assertEqual(self.entrar(SENHA_NOVA).status_code, 200)

    def test_troca_invalida_os_outros_links(self):
        primeiro = self.pedir_e_pegar_codigo()
        segundo = self.pedir_e_pegar_codigo()
        self.assertEqual(self.redefinir(segundo).status_code, 200)
        self.assertEqual(self.client.get(f"/api/v1/auth/reset-password/{primeiro}/").status_code, 410)

    def test_troca_encerra_as_sessoes_abertas(self):
        refresh = self.entrar(SENHA_ANTIGA).json()["refresh"]
        codigo = self.pedir_e_pegar_codigo()
        self.redefinir(codigo)
        self.assertTrue(BlacklistedToken.objects.exists())
        renovado = self.client.post("/api/v1/auth/refresh/", {"refresh": refresh}, format="json")
        self.assertEqual(renovado.status_code, 401)

    def test_aviso_de_senha_alterada(self):
        codigo = self.pedir_e_pegar_codigo()
        with self.captureOnCommitCallbacks(execute=True):
            self.redefinir(codigo)
        self.assertEqual(mail.outbox[-1].subject, "Jalapão Store: sua senha foi alterada")

    def test_senha_fraca_400_e_o_link_continua_valendo(self):
        codigo = self.pedir_e_pegar_codigo()
        resposta = self.redefinir(codigo, "12345678")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("password", resposta.json()["errors"])
        self.assertEqual(self.client.get(f"/api/v1/auth/reset-password/{codigo}/").status_code, 200)
        self.assertEqual(self.entrar(SENHA_ANTIGA).status_code, 200)

    def test_confirmacao_diferente_400(self):
        codigo = self.pedir_e_pegar_codigo()
        resposta = self.redefinir(codigo, SENHA_NOVA, "outra-coisa-qualquer-1")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("password_confirmation", resposta.json()["errors"])
        self.assertEqual(self.entrar(SENHA_ANTIGA).status_code, 200)


class DefinirEmailsTests(TestCase):
    def rodar(self, **ambiente) -> str:
        saida = StringIO()
        with mock.patch.dict("os.environ", ambiente, clear=False):
            call_command("definir_emails", stdout=saida, stderr=saida)
        return saida.getvalue()

    def setUp(self):
        self.jp = get_user_model().objects.create_user("jpmorais", password="x-senha-12345")
        self.admin = get_user_model().objects.create_user("admin", password="x-senha-12345")

    def test_preenche_so_o_jpmorais_quando_em_branco(self):
        self.rodar(JPMORAIS_EMAIL="dono@exemplo.com")
        self.jp.refresh_from_db()
        self.admin.refresh_from_db()
        self.assertEqual(self.jp.email, "dono@exemplo.com")
        self.assertEqual(self.admin.email, "")

    def test_preserva_e_mail_ja_cadastrado(self):
        self.jp.email = "antigo@exemplo.com"
        self.jp.save()
        self.rodar(JPMORAIS_EMAIL="dono@exemplo.com")
        self.jp.refresh_from_db()
        self.assertEqual(self.jp.email, "antigo@exemplo.com")

    def test_sem_variavel_ou_com_e_mail_invalido_nao_muda(self):
        self.rodar(JPMORAIS_EMAIL="")
        self.rodar(JPMORAIS_EMAIL="isso-nao-e-email")
        self.jp.refresh_from_db()
        self.assertEqual(self.jp.email, "")


class EspacosNaSenhaTests(TestCase):
    """A senha criada pelo link entra no login mesmo se foi digitada ou colada com espaço sobrando."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.usuario = get_user_model().objects.create_user(
            "jpmorais", email="dono@exemplo.com", password=SENHA_ANTIGA
        )

    def test_senha_com_espaco_nas_pontas_entra_no_login(self):
        self.client.post("/api/v1/auth/forgot-password/", {"email": "dono@exemplo.com"}, format="json")
        codigo = codigo_do_email(mail.outbox[-1])
        digitada = f"  {SENHA_NOVA}  "
        resposta = self.client.post(
            f"/api/v1/auth/reset-password/{codigo}/",
            {"password": digitada, "password_confirmation": digitada},
            format="json",
        )
        self.assertEqual(resposta.status_code, 200)
        for senha in (digitada, SENHA_NOVA):  # o login corta os espaços, com ou sem eles
            entrou = self.client.post(
                "/api/v1/auth/token/", {"username": "jpmorais", "password": senha}, format="json"
            )
            self.assertEqual(entrou.status_code, 200)
