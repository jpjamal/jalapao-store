"""Esqueci minha senha (spec 039).

- `pedir`: sempre termina igual para quem pediu (não revela se existe conta com aquele e-mail). Só
  com conta ativa, e-mail ligado e menos de 3 pedidos na última hora sai o e-mail com o link
  (1 hora, uso único; o banco guarda o hash).
- `redefinir`: troca a senha, usa o link, invalida os outros e encerra as sessões da pessoa (os
  refresh tokens vão para a lista de bloqueados). Depois avisa por e-mail que a senha mudou.
"""

import hashlib
import logging
import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from apps.accounts.models import PasswordReset
from apps.common.email import email_configurado, enviar, link_publico

logger = logging.getLogger(__name__)

VALIDADE = timedelta(hours=1)
MAX_POR_HORA = 3
INDISPONIVEL = "Este link não está mais disponível. Peça outro em “Esqueci minha senha”."


class RedefinicaoIndisponivel(APIException):
    """Vencido, usado, invalidado ou inexistente: a página não diz qual."""

    status_code = 410
    default_detail = INDISPONIVEL
    default_code = "redefinicao_indisponivel"


def hash_do_codigo(codigo: str) -> str:
    return hashlib.sha256(codigo.encode()).hexdigest()


def mascarar_email(email: str) -> str:
    nome, _, dominio = email.partition("@")
    return f"{nome[:2]}***@{dominio}"


def pedir(email: str) -> None:
    usuario = get_user_model().objects.filter(email__iexact=email.strip(), is_active=True).first()
    if usuario is None or not email_configurado():
        logger.info("senha.pedido_sem_envio")
        return
    recentes = PasswordReset.objects.filter(
        user=usuario, created_at__gte=timezone.now() - timedelta(hours=1)
    ).count()
    if recentes >= MAX_POR_HORA:
        logger.warning("senha.pedido_limite usuario_id=%s", usuario.pk)
        return
    codigo = secrets.token_hex(32)  # só [0-9a-f]: passa pela lista de rotas do BFF
    PasswordReset.objects.create(
        user=usuario, code_hash=hash_do_codigo(codigo), expires_at=timezone.now() + VALIDADE
    )
    texto = (
        f"Olá, {usuario.username}!\n\n"
        "Recebemos um pedido para criar uma senha nova na Jalapão Store. Para continuar, abra o link "
        f"(vale por 1 hora e pode ser usado uma vez):\n\n{link_publico(f'redefinir-senha/{codigo}')}"
        "\n\nSe não foi você, ignore este e-mail: sua senha continua a mesma."
    )
    enviar(usuario.email, "Jalapão Store: criar uma senha nova", texto, motivo="esqueci_senha")


def obter(codigo: str, *, travar: bool = False) -> PasswordReset:
    consulta = PasswordReset.objects.select_related("user")
    if travar:
        consulta = consulta.select_for_update(of=("self",))
    pedido = consulta.filter(code_hash=hash_do_codigo(codigo)).first()
    if (
        pedido is None
        or pedido.used_at is not None
        or pedido.invalidated_at is not None
        or pedido.expires_at <= timezone.now()
        or not pedido.user.is_active
    ):
        raise RedefinicaoIndisponivel()
    return pedido


@transaction.atomic
def redefinir(codigo: str, senha: str):
    pedido = obter(codigo, travar=True)
    usuario = pedido.user
    try:
        validate_password(senha, usuario)
    except DjangoValidationError as erro:
        raise ValidationError({"password": list(erro.messages)}) from erro
    momento = timezone.now()
    pedido.used_at = momento
    pedido.save(update_fields=["used_at"])
    usuario.set_password(senha)
    usuario.save(update_fields=["password"])
    PasswordReset.objects.filter(user=usuario, used_at__isnull=True, invalidated_at__isnull=True).update(
        invalidated_at=momento
    )
    # encerra as sessões abertas: os refresh tokens da pessoa vão para a lista de bloqueados
    for token in OutstandingToken.objects.filter(user=usuario):
        BlacklistedToken.objects.get_or_create(token=token)
    logger.info("senha.redefinida usuario_id=%s", usuario.pk)
    quando = timezone.localtime(momento).strftime("%d/%m/%Y às %H:%M")
    texto = (
        f"Olá, {usuario.username}!\n\n"
        f"A senha da sua conta na Jalapão Store foi alterada em {quando}. As sessões abertas foram "
        "encerradas.\n\nSe não foi você, avise o administrador do sistema."
    )
    if usuario.email:
        transaction.on_commit(
            lambda: enviar(
                usuario.email, "Jalapão Store: sua senha foi alterada", texto, motivo="senha_alterada"
            )
        )
    return usuario
