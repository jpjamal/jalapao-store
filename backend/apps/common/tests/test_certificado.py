"""O painel só avisa sobre o certificado se essa leitura funcionar de verdade."""

import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from django.test import TestCase
from apps.common import certificado


def gerar_certificado(pasta, dias):
    """Emite um certificado autoassinado que vence em `dias`; pula o teste sem openssl."""
    caminho = Path(pasta) / "fullchain.pem"
    chave = Path(pasta) / "key.pem"
    subprocess.run(
        [
            "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
            "-keyout", str(chave), "-out", str(caminho),
            "-days", str(dias), "-subj", "/CN=teste.jalapao",
        ],
        check=True,
        capture_output=True,
    )
    return caminho


class CertificadoTests(TestCase):
    def setUp(self):
        try:
            subprocess.run(["openssl", "version"], check=True, capture_output=True)
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("openssl indisponível neste ambiente.")

    def test_le_a_validade_e_decide_o_alerta(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = gerar_certificado(pasta, 30)
            estado = certificado.estado(caminho)
            self.assertIsNotNone(estado)
            self.assertGreater(estado["days_left"], 25)
            self.assertFalse(estado["alert"])

            # a poucos dias do vencimento o painel precisa gritar
            agora = datetime.now(timezone.utc) + timedelta(days=29)
            perto = certificado.estado(caminho, agora=agora)
            self.assertLessEqual(perto["days_left"], 2)
            self.assertTrue(perto["alert"])

    def test_certificado_ausente_nao_quebra_o_painel(self):
        self.assertIsNone(certificado.estado("/nao/existe/fullchain.pem"))

    def test_tenta_a_copia_legivel_antes_do_caminho_do_certbot(self):
        # o certbot cria live/ como 0700 de root; a cópia pública é a primeira tentativa
        self.assertEqual(
            certificado.caminhos_do_certificado()[0], "/certs/publico/cert.pem"
        )
        self.assertEqual(len(certificado.caminhos_do_certificado()), 2)

    def test_cai_para_o_segundo_caminho_quando_o_primeiro_falha(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = gerar_certificado(pasta, 30)
            original = certificado.CAMINHOS_PADRAO
            certificado.CAMINHOS_PADRAO = ("/nao/existe/cert.pem", str(caminho))
            try:
                self.assertIsNotNone(certificado.estado())
            finally:
                certificado.CAMINHOS_PADRAO = original

    def test_dashboard_responde_mesmo_sem_certificado(self):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Permission
        from rest_framework.test import APIClient

        user = get_user_model().objects.create_user("painel", password="conferindo-o-painel")
        user.user_permissions.set(
            Permission.objects.filter(
                codename__in=["view_product", "view_sale", "view_cashentry"]
            )
        )
        client = APIClient()
        client.force_authenticate(user)
        with self.settings():
            resposta = client.get("/api/v1/dashboard/")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("certificate", resposta.json())
