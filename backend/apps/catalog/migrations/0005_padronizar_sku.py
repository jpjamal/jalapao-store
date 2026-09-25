"""Spec 016 — dá o SKU no padrão atual (`SKU-<iniciais>-<número>`) aos produtos que ainda têm
o código do site anterior (ex.: `p_mu33g2qt_gy1hi`). Sem guardar o código antigo: o sistema
está em desenvolvimento e o dono pediu a troca simples.

A regra das iniciais é copiada aqui de propósito: migração não pode depender de código do app,
que muda com o tempo. Ela é a mesma de `catalog.models.sku_initials` em 25/09/2026.
"""

import re
import unicodedata

from django.db import migrations

PADRAO = re.compile(r"^SKU-[A-Z0-9]{1,6}-\d{4,}$")
LIGACAO = {"A", "AS", "DA", "DAS", "DE", "DO", "DOS", "E", "O", "OS", "PARA"}


def iniciais(nome):
    normalizado = unicodedata.normalize("NFKD", nome)
    sem_acento = "".join(c for c in normalizado if not unicodedata.combining(c)).upper()
    palavras = re.findall(r"[A-Z0-9]+", sem_acento)
    return "".join(p[0] for p in palavras if p not in LIGACAO)[:6] or "PRD"


def padronizar(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    SkuSequence = apps.get_model("catalog", "SkuSequence")
    for produto in Product.objects.order_by("created_at", "name", "id"):
        if PADRAO.match(produto.sku or ""):
            continue
        while True:  # mesma garantia do save(): número da sequência, nunca repetido
            candidato = f"SKU-{iniciais(produto.name)}-{SkuSequence.objects.create().pk:04d}"
            if not Product.objects.filter(sku=candidato).exists():
                break
        produto.sku = candidato
        produto.save(update_fields=["sku"])


class Migration(migrations.Migration):
    dependencies = [("catalog", "0004_publicacao_ml")]

    # sem volta: o código antigo não é guardado (decisão do dono, spec 016)
    operations = [migrations.RunPython(padronizar, migrations.RunPython.noop)]
