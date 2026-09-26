"""Desenvolvimento local: DEBUG ligado por padrão (desligue com DJANGO_DEBUG=0).

Uso: DJANGO_SETTINGS_MODULE=config.settings.development uv run python manage.py runserver"""

import os

from config.settings.base import *  # noqa: F403

DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = not DEBUG
