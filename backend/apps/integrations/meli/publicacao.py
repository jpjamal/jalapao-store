"""Publicação do rascunho no Mercado Livre (spec 012) — a única parte do sistema que cria ou
altera anúncio de verdade.

O rascunho é o lugar onde o anúncio é editado. `publicar` cria o anúncio a partir dele;
depois, `enviar_alteracoes` manda para o anúncio o que mudou no rascunho (preço, fotos,
atributos e descrição). As duas passam pelas mesmas peças: fotos, descrição e vínculo.

A ordem é pensada para falhar antes de mexer no anúncio: primeiro as conferências, depois as
fotos, e só então a chamada que cria ou altera. Se algo falhar antes, o anúncio fica como
estava; fotos que já subiram ficam soltas na conta do Mercado Livre e não aparecem para ninguém.
"""

from django.db import transaction
from django.utils import timezone

from apps.catalog.models import ListingDraft, Product

from ..base import IntegrationError
from .anuncio import (
    ajustar_envio,
    atributos_preenchidos,
    checagem_local,
    conta_do_mercado_livre,
    diagnosticar,
    montar_envio,
)

EXTENSAO = {"image/jpeg": "jpg", "image/png": "png"}


def _estoque(draft):
    try:
        return draft.product.stock.quantity
    except Product.stock.RelatedObjectDoesNotExist:
        return 0


def _mensagens(achados_ou_causas):
    return "; ".join(
        str(a.get("mensagem") or a.get("message") or a.get("code") or "")
        for a in achados_ou_causas
    )


def _erros(causas):
    return [c for c in causas if (c.get("type") or "error") == "error"] or causas


def _fotos(draft):
    return [ligacao.image for ligacao in draft.ordered_images.select_related("image").order_by("position")]


def _subir_fotos(conta, draft, conhecidas):
    """Ids das fotos do rascunho no Mercado Livre, na ordem do rascunho. Só sobe as que ainda
    não estão lá (`conhecidas`: id da foto da loja → id no Mercado Livre).
    Devolve `(ids, mapa_atualizado, quantas_subiram)`."""
    from apps.integrations.services import chamar

    mapa, ids, novas = dict(conhecidas or {}), [], 0
    for posicao, foto in enumerate(_fotos(draft), start=1):
        chave = str(foto.pk)
        if chave not in mapa:
            with foto.file.open("rb") as arquivo:
                conteudo = arquivo.read()
            mapa[chave] = chamar(
                conta, "upload_picture",
                filename=f"{draft.product.sku or 'produto'}-{posicao}.{EXTENSAO.get(foto.mime_type, 'jpg')}",
                content=conteudo,
                mime_type=foto.mime_type,
            )
            novas += 1
        ids.append(mapa[chave])
    return ids, mapa, novas


def _descricao(conta, item_id, texto):
    """Deixa a descrição do anúncio igual à do rascunho e confere o que ficou gravado.

    Cria quando o anúncio não tem descrição e substitui quando tem — POST em descrição
    existente dá 400. Não envia quando já está igual. Devolve um aviso, ou "" se deu certo."""
    from apps.integrations.services import chamar

    if not texto:
        return ""
    try:
        atual = chamar(conta, "get_description", item_id=item_id)
        if atual.strip() == texto:
            return ""
        chamar(conta, "set_description", item_id=item_id, text=texto, replace=bool(atual.strip()))
        if not chamar(conta, "get_description", item_id=item_id).strip():
            return ("O Mercado Livre aceitou a descrição, mas ela ainda não aparece no anúncio. "
                    "Envie de novo daqui a alguns minutos.")
        return ""
    except IntegrationError as exc:
        # o anúncio já existe: não desfazemos, avisamos para enviar de novo
        return f"A descrição não foi gravada no anúncio ({exc})."


def _resumo(listing, item, *, fotos, fotos_novas, avisos):
    return {
        "item_id": listing.item_id,
        "permalink": item.get("permalink") or "",
        "status": item.get("status") or "",
        "titulo": listing.title,
        "fotos": fotos,
        "fotos_novas": fotos_novas,
        "estoque": listing.remote_stock,
        "avisos": avisos,
    }


def _travar(draft_id):
    """Rascunho travado até o fim da transação: dois cliques não criam dois anúncios nem
    mandam duas alterações cruzadas."""
    draft = ListingDraft.objects.select_for_update().select_related("product").get(pk=draft_id)
    if draft.channel != ListingDraft.Channel.ML:
        raise IntegrationError("Este envio é do Mercado Livre; o rascunho é de outro canal.")
    return draft


def publicar(draft_id, *, actor=None):
    """Cria o anúncio a partir do rascunho e devolve o resumo.

    Recusa sem chamar o Mercado Livre quando o rascunho já foi publicado ou quando não há
    estoque: a simulação aceita 1 unidade de mentira, a publicação não — seria vender o que
    não existe. Estoque do anúncio é o estoque da loja no momento."""
    from apps.integrations.models import Listing

    with transaction.atomic():
        draft = _travar(draft_id)
        if Listing.objects.filter(draft=draft).exists():
            raise IntegrationError("Este rascunho já foi publicado.")
        estoque = _estoque(draft)
        if estoque <= 0:
            raise IntegrationError(
                "O produto está sem estoque. Registre a entrada no Estoque antes de publicar."
            )

        relatorio = diagnosticar(draft)
        if not relatorio["pode_publicar"]:
            raise IntegrationError(
                "O rascunho ainda não pode ser publicado: " + _mensagens(relatorio["erros"])
            )

        conta = conta_do_mercado_livre()
        ids, mapa, novas = _subir_fotos(conta, draft, {})

        envio = montar_envio(draft=draft, estoque=estoque)
        envio["available_quantity"] = estoque  # aqui vale o estoque real, sem o mínimo de 1
        envio["pictures"] = [{"id": i} for i in ids]
        (item, causas), envio = ajustar_envio(conta, envio, operacao="create_item")
        if not item:
            raise IntegrationError("O Mercado Livre recusou a publicação: " + _mensagens(_erros(causas)))

        aviso = _descricao(conta, item["id"], draft.description.strip())

        listing = Listing.objects.create(
            product=draft.product,
            marketplace="mercado_livre",
            seller_id=str(item.get("seller_id") or conta.external_id),
            item_id=str(item["id"]),
            user_product_id=str(item.get("user_product_id") or ""),
            family_id=str(item.get("family_id") or ""),
            title=str(item.get("title") or draft.title)[:300],
            remote_stock=item.get("available_quantity", estoque),
            draft=draft,
            pushed_at=timezone.now(),
            picture_ids=mapa,
        )

    return _resumo(listing, item, fotos=len(ids), fotos_novas=novas, avisos=[aviso] if aviso else [])


def enviar_alteracoes(draft_id, *, actor=None):
    """Manda para o anúncio já publicado o que está no rascunho: preço, fotos, atributos e
    descrição. Categoria e estoque não vão — categoria não muda depois de publicado, e o
    estoque segue a sincronização de Integrações. O título só vai em anúncio do modelo
    clássico; no modelo "produto do vendedor" quem monta o título é o Mercado Livre."""
    from apps.integrations.models import Listing
    from apps.integrations.services import chamar

    with transaction.atomic():
        draft = _travar(draft_id)
        listing = Listing.objects.select_for_update().filter(draft=draft).first()
        if not listing:
            raise IntegrationError("Este rascunho ainda não foi publicado.")

        conta = conta_do_mercado_livre()
        categoria = chamar(conta, "category", category_id=draft.category_id.strip())
        atributos = chamar(conta, "category_attributes", category_id=draft.category_id.strip())
        achados = checagem_local(
            draft=draft, fotos=_fotos(draft), categoria=categoria, atributos=atributos,
            estoque=_estoque(draft),
        )
        erros = [a for a in achados if a.nivel == "erro"]
        if erros:
            raise IntegrationError(
                "O rascunho tem problemas a corrigir antes de enviar: "
                + "; ".join(a.mensagem for a in erros)
            )

        ids, mapa, novas = _subir_fotos(conta, draft, listing.picture_ids)
        envio = {
            "price": float(draft.price),
            "pictures": [{"id": i} for i in ids],
            "attributes": [{"id": k, **v} for k, v in atributos_preenchidos(draft).items()],
        }
        if not listing.family_id:  # modelo clássico: o título é nosso
            envio["title"] = draft.title.strip()
        item, causas = chamar(conta, "update_item", item_id=listing.item_id, payload=envio)
        if not item:
            raise IntegrationError("O Mercado Livre recusou a alteração: " + _mensagens(_erros(causas)))

        aviso = _descricao(conta, listing.item_id, draft.description.strip())

        listing.title = str(item.get("title") or listing.title)[:300]
        listing.picture_ids = {k: v for k, v in mapa.items() if v in ids}
        listing.pushed_at = timezone.now()
        listing.save(update_fields=["title", "picture_ids", "pushed_at", "updated_at"])

    return _resumo(listing, item, fotos=len(ids), fotos_novas=novas, avisos=[aviso] if aviso else [])
