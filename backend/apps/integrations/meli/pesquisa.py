"""Pesquisa no Mercado Livre (spec 013): descobrir produtos e o que mais vende. Só leitura.

Duas consultas oficiais, com o token da conta conectada:
- produtos do catálogo por palavra-chave ou código de barras (`/products/search`);
- os 20 mais vendidos de uma categoria (`/highlights`), completados com nome, marca e foto.

Preço de concorrente não entra: na primeira pesquisa real (25/09/2026) todos os produtos
vieram como página tradicional, sem vendedor ganhando a página (`buy_box_winner: None`), e as
ofertas do produto responderam 404 "No winners found". A tela leva ao Mercado Livre para
conferir o preço lá.
"""

import urllib.parse

from ..base import IntegrationError
from .anuncio import conta_do_mercado_livre

BUSCA = "https://lista.mercadolivre.com.br/"


def _atributo(obj, atributo_id):
    for a in obj.get("attributes") or []:
        if a.get("id") == atributo_id:
            return a.get("value_name") or ""
    return ""


def _foto(obj):
    """Primeira foto: `pictures`, a variação escolhida em `pickers`, ou a miniatura."""
    fotos = obj.get("pictures") or []
    if fotos and isinstance(fotos[0], dict):
        return fotos[0].get("secure_url") or fotos[0].get("url") or ""
    for picker in obj.get("pickers") or []:
        opcoes = picker.get("products") or []
        escolhida = next((p for p in opcoes if p.get("product_id") == obj.get("id")), None) or (opcoes[:1] or [None])[0]
        if escolhida and escolhida.get("thumbnail"):
            return escolhida["thumbnail"]
    return obj.get("secure_thumbnail") or obj.get("thumbnail") or ""


def link(obj, nome):
    """O link do Mercado Livre quando vem; senão, a busca do site pelo nome — que sempre abre
    e mostra os anúncios com preço."""
    if obj.get("permalink"):
        return obj["permalink"]
    termo = " ".join(str(nome or "").split())[:120]
    return BUSCA + urllib.parse.quote(termo.replace(" ", "-")) if termo else ""


def _cartao(obj, ident, **extra):
    nome = obj.get("name") or obj.get("title") or obj.get("family_name") or ident
    return {
        "id": ident,
        "nome": nome,
        "familia": obj.get("family_name") or "",
        "marca": _atributo(obj, "BRAND"),
        "modelo": _atributo(obj, "MODEL"),
        "foto": _foto(obj),
        "link": link(obj, obj.get("family_name") or nome),
        **extra,
    }


def _detalhe(chamada):
    """Detalhe de um item do ranking. O Mercado Livre recusa (403) o detalhe de produto de
    outro vendedor; um item recusado não pode derrubar a lista inteira — fica sem detalhe."""
    try:
        return chamada() or {}
    except IntegrationError:
        return {}


def produtos(q="", gtin=""):
    """Produtos do catálogo que batem com a busca."""
    from apps.integrations.services import chamar

    conta = conta_do_mercado_livre()
    saida = []
    for achado in chamar(conta, "search_catalog", q=q, gtin=gtin, limit=10):
        produto_id = achado.get("id")
        if not produto_id:
            continue
        detalhe = chamar(conta, "product", product_id=produto_id) or achado
        saida.append(_cartao({**achado, **detalhe}, produto_id))
    return saida


def mais_vendidos(categoria_id):
    """Os 20 mais vendidos da categoria, na ordem. A lista do Mercado Livre traz só ids e tipo;
    nome, marca e foto vêm de uma segunda consulta, conforme o tipo: anúncio (ITEM), produto do
    catálogo (PRODUCT) ou produto do vendedor (USER_PRODUCT)."""
    from apps.integrations.services import chamar

    conta = conta_do_mercado_livre()
    destaques = chamar(conta, "best_sellers", category_id=categoria_id)
    ids_de_item = [d["id"] for d in destaques if d.get("type") == "ITEM" and d.get("id")]
    itens = {i["id"]: i for i in _detalhe(lambda: chamar(conta, "items", ids=ids_de_item)) or []} if ids_de_item else {}

    linhas = []
    for d in sorted(destaques, key=lambda d: d.get("position") or 99):
        tipo, ident = d.get("type") or "", d.get("id") or ""
        if tipo == "ITEM":
            fonte = itens.get(ident) or {}
        elif tipo == "PRODUCT":
            fonte = _detalhe(lambda: chamar(conta, "product", product_id=ident))
        else:  # USER_PRODUCT
            fonte = _detalhe(lambda: chamar(conta, "user_product", user_product_id=ident))
        cartao = _cartao(fonte, ident, posicao=d.get("position"), tipo=tipo, detalhado=bool(fonte))
        if not fonte:
            cartao["nome"] = "Produto de outro vendedor (detalhes não liberados)"
            cartao["link"] = ""  # sem nome não há o que buscar no site
        linhas.append(cartao)
    return {"itens": linhas}
