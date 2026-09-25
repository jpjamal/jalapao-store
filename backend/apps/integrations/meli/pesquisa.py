"""Pesquisa de preços no Mercado Livre (spec 013). Só leitura: nada é gravado, nada é enviado.

Três consultas oficiais, todas com o token da conta conectada:
- produtos do catálogo por palavra-chave ou código de barras (`/products/search`), cada um
  com o preço de quem está ganhando a página do produto;
- as ofertas de um produto do catálogo (`/products/{id}/items`), com o preço de cada vendedor;
- os 20 mais vendidos de uma categoria (`/highlights`), completados com nome e preço.

As respostas destas consultas ainda não foram vistas com a conta real. Por isso a leitura
de preço, nome e link é tolerante (procura nos campos conhecidos) e, quando não acha preço,
registra uma amostra no log para ajustar ao formato verdadeiro.
"""

import logging
from statistics import median

from .anuncio import conta_do_mercado_livre

logger = logging.getLogger(__name__)


def _numero(valor):
    try:
        return float(valor) if valor is not None and valor != "" else None
    except (TypeError, ValueError):
        return None


def preco_de(obj):
    """Preço em qualquer dos formatos conhecidos: `price`, `buy_box_winner.price`,
    `sale_price.amount` ou `price.amount`."""
    if not isinstance(obj, dict):
        return None
    for chave in ("price", "sale_price"):
        valor = obj.get(chave)
        if isinstance(valor, dict):
            valor = valor.get("amount")
        numero = _numero(valor)
        if numero is not None:
            return numero
    vencedor = obj.get("buy_box_winner")
    return preco_de(vencedor) if isinstance(vencedor, dict) else None


def _amostra(rotulo, obj):
    logger.warning("pesquisa de preços: %s sem preço reconhecido: %s", rotulo, str(obj)[:600])


def resumo(precos):
    """Menor, mediana, maior e quantidade — o que interessa para decidir preço."""
    validos = sorted(p for p in precos if p is not None)
    if not validos:
        return {"quantidade": 0, "menor": None, "mediana": None, "maior": None}
    return {
        "quantidade": len(validos),
        "menor": validos[0],
        "mediana": round(median(validos), 2),
        "maior": validos[-1],
    }


def _atributo(obj, atributo_id):
    for a in obj.get("attributes") or []:
        if a.get("id") == atributo_id:
            return a.get("value_name") or ""
    return ""


def _foto(obj):
    fotos = obj.get("pictures") or []
    if fotos and isinstance(fotos[0], dict):
        return fotos[0].get("secure_url") or fotos[0].get("url") or ""
    return obj.get("secure_thumbnail") or obj.get("thumbnail") or ""


def produtos(q="", gtin=""):
    """Produtos do catálogo que batem com a busca, cada um com o preço vencedor."""
    from apps.integrations.services import chamar

    conta = conta_do_mercado_livre()
    encontrados = chamar(conta, "search_catalog", q=q, gtin=gtin, limit=10)
    saida = []
    for achado in encontrados:
        produto_id = achado.get("id")
        if not produto_id:
            continue
        detalhe = chamar(conta, "product", product_id=produto_id) or {}
        preco = preco_de(detalhe)
        if preco is None:
            _amostra(f"produto {produto_id}", detalhe)
        vencedor = detalhe.get("buy_box_winner") or {}
        saida.append({
            "id": produto_id,
            "nome": detalhe.get("name") or achado.get("name") or produto_id,
            "marca": _atributo(detalhe or achado, "BRAND"),
            "modelo": _atributo(detalhe or achado, "MODEL"),
            "foto": _foto(detalhe),
            "preco_vencedor": preco,
            "frete_gratis": bool((vencedor.get("shipping") or {}).get("free_shipping")),
            "link": detalhe.get("permalink") or "",
        })
    return saida


def ofertas(produto_id):
    """As ofertas de um produto do catálogo, da mais barata para a mais cara."""
    from apps.integrations.services import chamar

    conta = conta_do_mercado_livre()
    itens = chamar(conta, "product_items", product_id=produto_id, limit=50)
    linhas = []
    for item in itens:
        preco = preco_de(item)
        if preco is None:
            _amostra(f"oferta de {produto_id}", item)
        envio = item.get("shipping") or {}
        linhas.append({
            "item_id": item.get("item_id") or item.get("id") or "",
            "preco": preco,
            "vendedor": str(item.get("seller_id") or ""),
            "condicao": item.get("condition") or "",
            "frete_gratis": bool(envio.get("free_shipping")),
            "tipo_anuncio": item.get("listing_type_id") or "",
            "full": envio.get("logistic_type") == "fulfillment",
        })
    linhas.sort(key=lambda linha: (linha["preco"] is None, linha["preco"] or 0))
    return {"resumo": resumo(linha["preco"] for linha in linhas), "ofertas": linhas}


def mais_vendidos(categoria_id):
    """Os 20 mais vendidos da categoria com nome e preço. A lista do Mercado Livre traz só
    ids e tipo; nome e preço vêm de uma segunda consulta, conforme o tipo:
    anúncio (ITEM), produto do catálogo (PRODUCT) ou produto do vendedor (USER_PRODUCT)."""
    from apps.integrations.services import chamar

    conta = conta_do_mercado_livre()
    destaques = chamar(conta, "best_sellers", category_id=categoria_id)
    ids_de_item = [d["id"] for d in destaques if d.get("type") == "ITEM" and d.get("id")]
    itens = {i["id"]: i for i in chamar(conta, "items", ids=ids_de_item)} if ids_de_item else {}

    linhas = []
    for d in sorted(destaques, key=lambda d: d.get("position") or 99):
        tipo, ident = d.get("type") or "", d.get("id") or ""
        if tipo == "ITEM":
            fonte = itens.get(ident) or {}
            nome, link = fonte.get("title") or ident, fonte.get("permalink") or ""
        elif tipo == "PRODUCT":
            fonte = chamar(conta, "product", product_id=ident) or {}
            nome, link = fonte.get("name") or ident, fonte.get("permalink") or ""
        else:  # USER_PRODUCT
            fonte = chamar(conta, "user_product", user_product_id=ident) or {}
            nome, link = fonte.get("name") or fonte.get("family_name") or ident, fonte.get("permalink") or ""
        preco = preco_de(fonte)
        if preco is None:
            _amostra(f"{tipo} {ident}", fonte)
        linhas.append({
            "posicao": d.get("position"),
            "id": ident,
            "tipo": tipo,
            "nome": nome,
            "preco": preco,
            "foto": _foto(fonte),
            "link": link,
        })
    return {"resumo": resumo(linha["preco"] for linha in linhas), "itens": linhas}
