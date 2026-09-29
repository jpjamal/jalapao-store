"""Código de barras do produto: GTIN-8, 12, 13 (EAN) ou 14, com dígito verificador (spec 021)."""

import re

TAMANHOS = {8, 12, 13, 14}


def normalize_gtin(value: str) -> str:
    """Tira espaços e hífens que o leitor ou a digitação podem deixar."""
    return re.sub(r"[\s-]", "", value or "")


def check_digit(body: str) -> int:
    """Dígito verificador GS1: pesos 3 e 1 da direita para a esquerda, sobre o corpo sem ele."""
    total = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(body)))
    return (10 - total % 10) % 10


def gtin_error(code: str) -> str | None:
    """Mensagem de erro para um código já normalizado, ou None se for válido."""
    if not code.isdigit():
        return "Use apenas números."
    if len(code) not in TAMANHOS:
        return "O código de barras deve ter 8, 12, 13 ou 14 dígitos."
    if check_digit(code[:-1]) != int(code[-1]):
        return "Dígito verificador inválido: confira o código de barras."
    return None
