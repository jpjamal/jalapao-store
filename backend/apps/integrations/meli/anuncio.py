"""Validação de rascunho de anúncio contra o Mercado Livre — spec 011.

Duas fontes, um relatório:

- **checagem local**: o que dá para saber sem perguntar ao Mercado Livre sobre o anúncio
  (campos preenchidos, fotos, limites da categoria, atributos obrigatórios);
- **simulação**: `POST /items/validate`, que confere o anúncio inteiro sem criá-lo.

Nada aqui publica, envia foto ou mexe em estoque. As funções de regra são puras — recebem
dados já lidos e devolvem achados — para serem testadas sem rede.
"""

from dataclasses import asdict, dataclass

from apps.catalog.models import ListingDraft, Product

# Requisitos de imagem publicados em "Imagens" na documentação do Mercado Livre
FORMATOS_ACEITOS = {"image/jpeg", "image/png"}
LADO_MINIMO = 500        # abaixo disso o Mercado Livre não amplia a foto
LADO_RECOMENDADO = 1200  # tamanho em que ele recomenda carregar
TITULO_PADRAO = 60       # usado se a categoria não informar o próprio limite
TIPO_DE_ANUNCIO = "gold_special"  # Clássico; Premium é escolha da publicação (entrega 3)


@dataclass
class Achado:
    nivel: str      # "erro" impede publicar; "aviso" não impede
    origem: str     # "local" ou "mercado_livre"
    campo: str
    mensagem: str
    codigo: str = ""


def _erro(campo, mensagem, codigo=""):
    return Achado("erro", "local", campo, mensagem, codigo)


def _aviso(campo, mensagem, codigo=""):
    return Achado("aviso", "local", campo, mensagem, codigo)


# ---------- atributos ----------


def tags_de(atributo):
    """As tags vêm como objeto (`{"required": true}`) ou como lista (`["required"]`),
    conforme o endpoint e a época da API. Devolve sempre um conjunto de nomes."""
    tags = atributo.get("tags") or {}
    if isinstance(tags, dict):
        return {nome for nome, ligado in tags.items() if ligado}
    if isinstance(tags, list):
        return {str(nome) for nome in tags}
    return set()


def atributos_do_formulario(atributos):
    """O que a tela mostra: sem ocultos e sem somente leitura, obrigatórios primeiro."""
    visiveis = []
    for a in atributos:
        tags = tags_de(a)
        if {"hidden", "read_only"} & tags:
            continue
        visiveis.append({
            "id": a.get("id"),
            "name": a.get("name") or a.get("id"),
            "value_type": a.get("value_type") or "string",
            "value_max_length": a.get("value_max_length"),
            "values": [{"id": str(v.get("id")), "name": v.get("name")} for v in (a.get("values") or [])],
            "allowed_units": [u.get("id") for u in (a.get("allowed_units") or [])],
            "default_unit": a.get("default_unit"),
            "required": "required" in tags,
            "conditional_required": "conditional_required" in tags,
            "catalog_required": "catalog_required" in tags,
        })
    visiveis.sort(key=lambda a: (not a["required"], not a["conditional_required"], a["name"] or ""))
    return visiveis


def valor_do_rascunho(bruto):
    """O rascunho guarda o atributo como texto ou como {"value_id", "value_name"}."""
    if bruto is None:
        return None
    if isinstance(bruto, dict):
        vid = str(bruto.get("value_id") or "").strip()
        vname = str(bruto.get("value_name") or "").strip()
        if not vid and not vname:
            return None
        return {k: v for k, v in (("value_id", vid), ("value_name", vname)) if v}
    texto = str(bruto).strip()
    return {"value_name": texto} if texto else None


def atributos_preenchidos(draft):
    """Atributos do rascunho no formato do Mercado Livre, com marca e modelo das colunas."""
    preenchidos = {}
    for chave, bruto in (draft.attributes or {}).items():
        valor = valor_do_rascunho(bruto)
        if valor:
            preenchidos[str(chave)] = valor
    # marca e modelo têm coluna própria no rascunho; só entram se o formulário não tiver
    if draft.brand.strip() and "BRAND" not in preenchidos:
        preenchidos["BRAND"] = {"value_name": draft.brand.strip()}
    if draft.model.strip() and "MODEL" not in preenchidos:
        preenchidos["MODEL"] = {"value_name": draft.model.strip()}
    return preenchidos


# ---------- regras da categoria ----------


def _config(categoria, chave, padrao=None):
    """Os limites da categoria vêm em `settings`; tolera também no nível de cima."""
    settings = categoria.get("settings") or {}
    if chave in settings and settings[chave] is not None:
        return settings[chave]
    valor = categoria.get(chave)
    return padrao if valor is None else valor


# ---------- checagem local ----------


def checagem_local(*, draft, fotos, categoria, atributos, estoque):
    """Achados que não dependem de simular o anúncio. `fotos` já vem na ordem do rascunho."""
    achados = []

    titulo = draft.title.strip()
    if not titulo:
        achados.append(_erro("title", "Informe o título do anúncio."))
    else:
        limite = int(_config(categoria, "max_title_length", TITULO_PADRAO) or TITULO_PADRAO)
        if len(titulo) > limite:
            achados.append(_erro("title", f"O título tem {len(titulo)} caracteres; a categoria aceita até {limite}."))

    if draft.price is None or draft.price <= 0:
        achados.append(_erro("price", "Informe o preço do anúncio."))
    else:
        minimo = _config(categoria, "minimum_price")
        if minimo not in (None, "") and float(draft.price) < float(minimo):
            achados.append(_erro("price", f"A categoria exige preço mínimo de R$ {float(minimo):.2f}."))

    if not draft.category_id.strip():
        achados.append(_erro("category_id", "Escolha a categoria do Mercado Livre."))
    elif categoria and _config(categoria, "listing_allowed", True) is False:
        achados.append(_erro(
            "category_id",
            "Esta categoria não aceita anúncio — escolha uma categoria final, mais específica.",
        ))

    if not draft.condition:
        achados.append(_aviso("condition", "Condição não informada; a simulação considera Novo."))

    if not draft.description.strip():
        achados.append(_aviso("description", "Descrição vazia. Não impede publicar, mas pesa na venda."))

    if estoque <= 0:
        achados.append(_aviso(
            "stock",
            "Estoque do produto é zero. Publicar exige ao menos uma unidade; a simulação usa 1.",
        ))

    # fotos
    if not fotos:
        achados.append(_erro("images", "Escolha ao menos uma foto para o anúncio."))
    else:
        maximo = _config(categoria, "max_pictures_per_item")
        if maximo and len(fotos) > int(maximo):
            achados.append(_erro("images", f"{len(fotos)} fotos escolhidas; a categoria aceita até {maximo}."))
        for posicao, foto in enumerate(fotos, start=1):
            nome = f"Foto {posicao}"
            if foto.mime_type not in FORMATOS_ACEITOS:
                achados.append(_erro(
                    "images", f"{nome} está em {foto.mime_type}; o Mercado Livre aceita JPG ou PNG."
                ))
            menor = min(foto.width, foto.height)
            if menor < LADO_MINIMO:
                achados.append(_aviso(
                    "images",
                    f"{nome} tem {foto.width}×{foto.height}; abaixo de {LADO_MINIMO}×{LADO_MINIMO} "
                    "o Mercado Livre não amplia e ela aparece pequena.",
                ))
            elif menor < LADO_RECOMENDADO:
                achados.append(_aviso(
                    "images",
                    f"{nome} tem {foto.width}×{foto.height}; o recomendado é "
                    f"{LADO_RECOMENDADO}×{LADO_RECOMENDADO}.",
                ))

    # atributos da categoria
    preenchidos = atributos_preenchidos(draft)
    for a in atributos:
        tags = tags_de(a)
        if {"hidden", "read_only"} & tags:
            continue
        if a.get("id") in preenchidos:
            continue
        nome = a.get("name") or a.get("id")
        if "required" in tags:
            achados.append(_erro(f"attributes.{a.get('id')}", f"Atributo obrigatório sem valor: {nome}."))
        elif "conditional_required" in tags:
            achados.append(_aviso(
                f"attributes.{a.get('id')}", f"{nome} pode ser exigido conforme o produto."
            ))
    return achados


# ---------- simulação ----------


def montar_envio(*, draft, estoque):
    """O corpo que a simulação envia. Custo interno nunca entra. Sem fotos e sem descrição:
    as fotos são privadas e a descrição vai em chamada própria depois de criado o anúncio."""
    envio = {
        "title": draft.title.strip(),
        "category_id": draft.category_id.strip(),
        "price": float(draft.price) if draft.price is not None else None,
        "currency_id": "BRL",
        "available_quantity": max(int(estoque), 1),
        "buying_mode": "buy_it_now",
        "listing_type_id": TIPO_DE_ANUNCIO,
        "condition": draft.condition or "new",
        "attributes": [{"id": k, **v} for k, v in atributos_preenchidos(draft).items()],
    }
    return {k: v for k, v in envio.items() if v not in (None, "")}


def _campos_citados(causas, codigo):
    """Campos que as causas com esse código citam, por referência ou na mensagem."""
    campos = set()
    for c in causas:
        if (c.get("code") or "") != codigo:
            continue
        texto = " ".join([str(c.get("message") or ""), *(str(r) for r in (c.get("references") or []))])
        campos.update(nome for nome in ("family_name", "title") if nome in texto)
    return campos


def simular(conta, envio):
    """Chama a simulação e se ajusta ao modelo de anúncio da conta.

    Contas no modelo "produto do vendedor" (User Products) pedem `family_name`, o nome do
    produto sem variação, e montam o título sozinhas, recusando `title`. Como isso depende da
    conta e não da categoria, a simulação tenta o formato clássico e corrige conforme a
    resposta — no máximo duas vezes, sempre só consultando."""
    from apps.integrations.services import chamar

    causas = chamar(conta, "validate_item", payload=envio)
    for _ in range(2):
        faltando = _campos_citados(causas, "body.required_fields")
        sobrando = _campos_citados(causas, "body.invalid_fields")
        if "family_name" in faltando and "family_name" not in envio:
            envio = {**envio, "family_name": envio.get("title", "")}
        elif "title" in sobrando and "title" in envio:
            envio = {k: v for k, v in envio.items() if k != "title"}
        else:
            break
        causas = chamar(conta, "validate_item", payload=envio)
    return causas


def _e_de_foto(causa):
    """Causas que existem só porque a simulação vai sem fotos."""
    texto = " ".join([
        str(causa.get("code") or ""),
        " ".join(str(r) for r in (causa.get("references") or [])),
    ]).lower()
    return "picture" in texto


def achados_do_mercado_livre(causas):
    """Traduz as causas da simulação. `error` bloqueia, `warning` não.
    Devolve também quantas causas de foto foram retiradas."""
    achados, retiradas = [], 0
    for c in causas:
        if _e_de_foto(c):
            retiradas += 1
            continue
        nivel = "erro" if str(c.get("type") or "error").lower() == "error" else "aviso"
        referencias = c.get("references") or []
        achados.append(Achado(
            nivel=nivel,
            origem="mercado_livre",
            campo=str(referencias[0]) if referencias else "",
            mensagem=str(c.get("message") or c.get("code") or "Sem detalhe."),
            codigo=str(c.get("code") or ""),
        ))
    return achados, retiradas


# ---------- orquestração ----------


def conta_do_mercado_livre():
    from apps.integrations.base import IntegrationError
    from apps.integrations.models import MarketplaceAccount

    conta = MarketplaceAccount.objects.filter(
        channel=MarketplaceAccount.Channel.ML, active=True
    ).first()
    if not conta:
        raise IntegrationError("Conecte uma conta do Mercado Livre em Integrações antes de validar.")
    return conta


def diagnosticar(draft):
    """Relatório completo do rascunho. Não publica nada."""
    from apps.integrations.base import IntegrationError
    from apps.integrations.services import chamar

    if draft.channel != ListingDraft.Channel.ML:
        raise IntegrationError("Esta validação é do Mercado Livre; o rascunho é de outro canal.")

    fotos = [ligacao.image for ligacao in draft.ordered_images.select_related("image").order_by("position")]
    try:
        estoque = draft.product.stock.quantity
    except Product.stock.RelatedObjectDoesNotExist:  # produto ainda sem registro de estoque
        estoque = 0

    conta = None
    categoria, atributos = {}, []
    if draft.category_id.strip():
        conta = conta_do_mercado_livre()
        categoria = chamar(conta, "category", category_id=draft.category_id.strip())
        atributos = chamar(conta, "category_attributes", category_id=draft.category_id.strip())

    achados = checagem_local(
        draft=draft, fotos=fotos, categoria=categoria, atributos=atributos, estoque=estoque
    )

    # Só vale simular se o básico estiver lá; senão o Mercado Livre repetiria os mesmos erros.
    basico = not any(a.nivel == "erro" and a.campo in ("title", "price", "category_id") for a in achados)
    simulado, retiradas = False, 0
    if basico:
        conta = conta or conta_do_mercado_livre()
        causas = simular(conta, montar_envio(draft=draft, estoque=estoque))
        remotos, retiradas = achados_do_mercado_livre(causas)
        achados.extend(remotos)
        simulado = True

    erros = [a for a in achados if a.nivel == "erro"]
    return {
        "pode_publicar": simulado and not erros,
        "simulado_no_mercado_livre": simulado,
        "causas_de_foto_retiradas": retiradas,
        "categoria": {
            "id": categoria.get("id") or draft.category_id,
            "nome": categoria.get("name") or "",
            "caminho": [p.get("name") for p in (categoria.get("path_from_root") or [])],
        } if draft.category_id.strip() else None,
        "erros": [asdict(a) for a in erros],
        "avisos": [asdict(a) for a in achados if a.nivel == "aviso"],
    }
