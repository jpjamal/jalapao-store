"""Quanto falta para o certificado HTTPS vencer.

O certificado é emitido para IP com o perfil shortlived do Let's Encrypt: dura
cerca de seis dias e o certbot tenta renovar a cada doze horas. Se a renovação
falhar em silêncio, o site sai do ar em menos de uma semana — e até agora não
havia nenhum aviso. O painel passa a mostrar os dias restantes.

A leitura é do arquivo montado em volume, não de uma conexão: o que interessa é
o certificado que o proxy vai servir na próxima renovação, atualizado pelo
certbot mesmo quando ninguém acessa o site.

`ssl._ssl._test_decode_cert` é API privada do CPython, e é o único jeito de ler a
validade de um PEM sem trazer a dependência `cryptography` só para isso. Está
isolado aqui e protegido: se algum dia sumir, a função devolve None e o painel
simplesmente não mostra o aviso — nada quebra.
"""

import os
import ssl
from datetime import datetime, timezone

CAMINHO_PADRAO = "/certs/live/jalapao-ip/fullchain.pem"
DIAS_DE_ALERTA_PADRAO = 2


def caminho_do_certificado():
    return os.getenv("TLS_CERT_PATH", CAMINHO_PADRAO)


def dias_de_alerta():
    try:
        return int(os.getenv("TLS_ALERT_DAYS", DIAS_DE_ALERTA_PADRAO))
    except ValueError:
        return DIAS_DE_ALERTA_PADRAO


def vencimento(caminho=None):
    """Data de expiração do certificado, ou None quando não dá para ler."""
    caminho = caminho or caminho_do_certificado()
    try:
        dados = ssl._ssl._test_decode_cert(caminho)
        return datetime.strptime(dados["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(
            tzinfo=timezone.utc
        )
    except Exception:
        # sem certificado (desenvolvimento), sem permissão, formato inesperado
        return None


def estado(caminho=None, agora=None):
    """{'expires_at', 'days_left', 'alert'} — ou None quando não há o que informar."""
    fim = vencimento(caminho)
    if fim is None:
        return None
    agora = agora or datetime.now(timezone.utc)
    restam = (fim - agora).days
    return {
        "expires_at": fim.isoformat(),
        "days_left": restam,
        "alert": restam <= dias_de_alerta(),
    }
