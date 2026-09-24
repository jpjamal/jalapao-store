"""Autorizações perto de vencer.

A autorização de uma loja dura no máximo 365 dias na Shopee, e vencer significa a
integração parar calada — o token renova normalmente até o dia em que não renova mais.
O painel avisa antes, do mesmo jeito que avisa do certificado.

Fica em módulo próprio para o painel não precisar conhecer o modelo de integração, e para
o limiar ser um só, usado pela API e pela tela.
"""

import os

DIAS_DE_ALERTA_PADRAO = 15


def dias_de_alerta():
    try:
        return int(os.getenv("MARKETPLACE_ALERT_DAYS", DIAS_DE_ALERTA_PADRAO))
    except ValueError:
        return DIAS_DE_ALERTA_PADRAO


def autorizacoes_a_vencer():
    """Contas ativas cuja autorização vence dentro do limiar. Lista vazia é o normal."""
    from .models import MarketplaceAccount

    limite = dias_de_alerta()
    avisos = []
    for conta in MarketplaceAccount.objects.filter(
        active=True, authorization_expires_at__isnull=False
    ):
        faltam = conta.dias_ate_expirar_autorizacao
        if faltam is not None and faltam <= limite:
            avisos.append(
                {
                    "channel": conta.channel,
                    "channel_label": conta.get_channel_display(),
                    "name": conta.name or conta.external_id,
                    "days_left": faltam,
                    "expires_at": conta.authorization_expires_at.isoformat(),
                }
            )
    return avisos
