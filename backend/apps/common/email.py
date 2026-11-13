"""E-mail do sistema (spec 039): texto simples, pt-BR, remetente "Jalapão Store".

`enviar` nunca levanta erro: devolve se saiu. Quem chama decide o que fazer com a falha (o
"esqueci minha senha" só registra no log). O endereço do destinatário não vai para o log (LGPD).
"""

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def email_configurado() -> bool:
    return bool(
        settings.EMAIL_SEM_SMTP or (settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD)
    )


def link_publico(caminho: str) -> str:
    """Link absoluto para o e-mail (`URL_PUBLICA` já traz o prefixo /jalapao-store)."""
    return f"{settings.URL_PUBLICA}/{caminho.lstrip('/')}"


def enviar(para: str, assunto: str, texto: str, *, motivo: str) -> bool:
    if not email_configurado():
        logger.info("email.desligado motivo=%s", motivo)
        return False
    try:
        send_mail(assunto, texto, settings.DEFAULT_FROM_EMAIL, [para], fail_silently=False)
    except Exception as erro:  # SMTP, rede, tempo: o sistema segue sem o e-mail
        logger.warning("email.falhou motivo=%s erro=%s", motivo, type(erro).__name__)
        return False
    logger.info("email.enviado motivo=%s", motivo)
    return True
