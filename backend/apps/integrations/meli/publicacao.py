"""Publicação do rascunho no Mercado Livre (spec 012) — a única parte do sistema que cria
anúncio de verdade.

A ordem é pensada para falhar antes de criar: primeiro a mesma validação da spec 011 (local
e simulada), depois as fotos, e só então `POST /items`. Se algo falhar antes do anúncio
existir, nada fica publicado; as fotos que já subiram ficam soltas na conta do Mercado Livre,
sem anúncio, e não aparecem para ninguém.
"""

from django.db import transaction

from apps.catalog.models import ListingDraft, Product

from ..base import IntegrationError
from .anuncio import (
    ajustar_envio,
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


def publicar(draft_id, *, actor=None):
    """Publica o rascunho e devolve o resumo do anúncio criado.

    Recusa sem chamar o Mercado Livre quando o rascunho já foi publicado ou quando não há
    estoque: a simulação aceita 1 unidade de mentira, a publicação não — seria vender o que
    não existe. Estoque do anúncio é o estoque da loja no momento."""
    from apps.integrations.models import Listing
    from apps.integrations.services import chamar

    with transaction.atomic():
        # trava o rascunho: dois cliques em "Publicar" não criam dois anúncios
        draft = ListingDraft.objects.select_for_update().select_related("product").get(pk=draft_id)
        if draft.channel != ListingDraft.Channel.ML:
            raise IntegrationError("Esta publicação é do Mercado Livre; o rascunho é de outro canal.")
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
        fotos = [
            ligacao.image
            for ligacao in draft.ordered_images.select_related("image").order_by("position")
        ]
        ids_das_fotos = []
        for posicao, foto in enumerate(fotos, start=1):
            with foto.file.open("rb") as arquivo:
                conteudo = arquivo.read()
            ids_das_fotos.append(chamar(
                conta, "upload_picture",
                filename=f"{draft.product.sku or 'produto'}-{posicao}.{EXTENSAO.get(foto.mime_type, 'jpg')}",
                content=conteudo,
                mime_type=foto.mime_type,
            ))

        envio = montar_envio(draft=draft, estoque=estoque)
        envio["available_quantity"] = estoque  # aqui vale o estoque real, sem o mínimo de 1
        envio["pictures"] = [{"id": i} for i in ids_das_fotos]
        (item, causas), envio = ajustar_envio(conta, envio, operacao="create_item")
        if not item:
            erros = [c for c in causas if (c.get("type") or "error") == "error"] or causas
            raise IntegrationError("O Mercado Livre recusou a publicação: " + _mensagens(erros))

        avisos = []
        if draft.description.strip():
            try:
                chamar(conta, "set_description", item_id=item["id"], text=draft.description.strip())
            except IntegrationError as exc:
                # o anúncio já existe: não desfazemos, avisamos para completar pelo Mercado Livre
                avisos.append(f"O anúncio foi criado, mas a descrição não foi gravada ({exc}).")

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
        )

    return {
        "item_id": listing.item_id,
        "permalink": item.get("permalink") or "",
        "status": item.get("status") or "",
        "titulo": listing.title,
        "fotos": len(ids_das_fotos),
        "estoque": listing.remote_stock,
        "avisos": avisos,
    }
