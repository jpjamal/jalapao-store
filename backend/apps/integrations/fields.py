"""Campo para segredos de marketplace cifrados no banco.

A chave deriva do DJANGO_SECRET_KEY, que deve continuar estável e fora do repositório.
O prefixo distingue dados cifrados; texto legado é convertido pela migração 0004.
"""

import base64

from cryptography.exceptions import InvalidKey
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from django.conf import settings
from django.db import models

PREFIXO = "enc:v1:"


class TokenDecryptionError(ValueError):
    """O segredo configurado não consegue ler o token; valor armazenado não é exibido."""


def _fernet():
    segredo = settings.SECRET_KEY.encode("utf-8")
    chave = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"jalapao-store-marketplace-tokens-v1",
        info=b"django-model-fields",
    ).derive(segredo)
    try:
        return Fernet(base64.urlsafe_b64encode(chave))
    except (InvalidKey, ValueError) as exc:
        raise TokenDecryptionError("Chave de tokens inválida.") from exc


def cifrar(valor):
    if not valor:
        return valor
    return PREFIXO + _fernet().encrypt(valor.encode("utf-8")).decode("ascii")


def decifrar(valor):
    if not valor:
        return valor
    if not valor.startswith(PREFIXO):
        raise TokenDecryptionError("Token armazenado sem criptografia; migração pendente.")
    try:
        return _fernet().decrypt(valor[len(PREFIXO):].encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeError, ValueError) as exc:
        raise TokenDecryptionError("Não foi possível decifrar o token; confira DJANGO_SECRET_KEY.") from exc


class EncryptedTextField(models.TextField):
    """Persiste cifrado; expõe texto claro somente dentro do processo Django."""

    def from_db_value(self, value, expression, connection):
        return decifrar(value)

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return cifrar(value)
