"""Produção — o padrão de `manage.py` e do `wsgi`. Igual à base: tudo o que é sensível
(DEBUG, hosts, banco, origens) já vem das variáveis de ambiente do deploy."""

from config.settings.base import *  # noqa: F403
