"""Testes: hash de senha rápido e arquivos de mídia num diretório temporário.
O CI usa este módulo (DJANGO_SETTINGS_MODULE=config.settings.test)."""

import tempfile

from config.settings.base import *  # noqa: F403

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
MEDIA_ROOT = tempfile.mkdtemp(prefix="jalapao-media-teste-")
