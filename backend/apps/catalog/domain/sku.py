"""Formação do SKU automático: `SKU-<iniciais>-<número>` (specs 010 e 016)."""

import re
import unicodedata

PALAVRAS_DE_LIGACAO = {"A", "AS", "DA", "DAS", "DE", "DO", "DOS", "E", "O", "OS", "PARA"}


def sku_initials(name: str) -> str:
    """Iniciais do nome, sem acento e sem palavras de ligação, até 6 letras (`PRD` se vazio)."""
    normalized = unicodedata.normalize("NFKD", name)
    words = re.findall(r"[A-Z0-9]+", "".join(c for c in normalized if not unicodedata.combining(c)).upper())
    initials = "".join(word[0] for word in words if word not in PALAVRAS_DE_LIGACAO)
    return initials[:6] or "PRD"


def sku(initials: str, number: int) -> str:
    return f"SKU-{initials}-{number:04d}"
