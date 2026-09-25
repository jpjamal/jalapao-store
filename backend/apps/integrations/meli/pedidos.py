"""Vendas do Mercado Livre para a loja, sob comando do dono (spec 015).

Nada é automático: o dono pede a prévia, confere e manda importar. Cada pedido pago vira uma
venda do canal Mercado Livre pela mesma regra da venda manual (`create_sale`): baixa o estoque
pelo custo médio, calcula o líquido com a taxa e o frete reais e fica "a receber" até o dono
marcar o recebimento, que é quando entra no caixa. Pedido cancelado no Mercado Livre cancela a
venda importada (`cancel_sale`), devolvendo o estoque.

Um pedido vira no máximo uma venda: a venda guarda o código do pedido (`external_id`, único
por canal) e a chave de idempotência é derivada dele.
"""

import uuid
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from ..base import IntegrationError
from .anuncio import conta_do_mercado_livre

CANAL = "mercado_livre"
LIMITE = 200  # pedidos por consulta, somando as páginas


def _dinheiro(valor):
    try:
        return Decimal(str(valor or 0)).quantize(Decimal("0.01"))
    except (ArithmeticError, ValueError):
        return Decimal("0.00")


def _vinculos():
    """Anúncio do Mercado Livre → produto da loja, pelo vínculo já existente em Integrações."""
    from apps.integrations.models import Listing

    return {
        v.item_id: v.product
        for v in Listing.objects.select_related("product").filter(marketplace=CANAL)
    }


def _venda(order_id):
    from apps.sales.models import Sale

    return Sale.objects.filter(channel=CANAL, external_id=str(order_id)).first()


def taxa_do_pedido(pedido):
    """Comissão do Mercado Livre no pedido. Preferência: `marketplace_fee` dos pagamentos, que
    é o valor total cobrado; na falta, `sale_fee` de cada item vezes a quantidade."""
    pagamentos = [p for p in pedido.get("payments") or [] if p.get("marketplace_fee") is not None]
    if pagamentos:
        return sum((_dinheiro(p["marketplace_fee"]) for p in pagamentos), Decimal("0.00"))
    return sum(
        (_dinheiro(i.get("sale_fee")) * int(i.get("quantity") or 0) for i in pedido.get("order_items") or []),
        Decimal("0.00"),
    )


def frete_do_vendedor(conta, pedido):
    """Quanto do frete coube ao vendedor. None quando não deu para ler — a prévia avisa."""
    from apps.integrations.services import chamar

    envio_id = (pedido.get("shipping") or {}).get("id")
    if not envio_id:
        return Decimal("0.00")
    try:
        custos = chamar(conta, "shipment_costs", shipment_id=envio_id)
    except IntegrationError:
        return None
    remetentes = custos.get("senders") or []
    if not remetentes:
        return None
    return sum((_dinheiro(r.get("cost")) for r in remetentes), Decimal("0.00"))


def ler_pedido(pedido, vinculos, frete):
    """O pedido no formato da loja, com o que impede importar em `problemas`."""
    itens, problemas, por_produto = [], [], {}
    for linha in pedido.get("order_items") or []:
        item = linha.get("item") or {}
        produto = vinculos.get(item.get("id"))
        quantidade = int(linha.get("quantity") or 0)
        preco = _dinheiro(linha.get("unit_price"))
        itens.append({
            "item_id": item.get("id") or "",
            "titulo": item.get("title") or "",
            "quantidade": quantidade,
            "preco": preco,
            "produto_id": str(produto.id) if produto else None,
            "produto": produto.name if produto else "",
        })
        if not produto:
            problemas.append(f"Anúncio {item.get('id')} sem produto vinculado em Integrações.")
        elif not produto.active:
            problemas.append(f"Produto {produto.name} está inativo.")
        elif produto.id in por_produto and por_produto[produto.id] != preco:
            problemas.append(f"{produto.name} aparece duas vezes com preços diferentes.")
        elif produto:
            por_produto[produto.id] = preco
    bruto = sum((i["preco"] * i["quantidade"] for i in itens), Decimal("0.00"))
    taxa = taxa_do_pedido(pedido)
    avisos = [] if frete is not None else [
        "Frete não lido no Mercado Livre: a venda entra com frete zero. Confira no painel."
    ]
    return {
        "order_id": str(pedido.get("id") or ""),
        "data": pedido.get("date_created") or "",
        "status": pedido.get("status") or "",
        "itens": itens,
        "bruto": bruto,
        "taxa": taxa,
        "frete": frete,
        "liquido": bruto - taxa - (frete or Decimal("0.00")),
        "problemas": problemas,
        "avisos": avisos,
    }


def _situacao(lido):
    venda = _venda(lido["order_id"])
    if lido["status"] == "cancelled":
        return "cancelar" if venda and venda.status == "confirmed" else None
    if lido["status"] != "paid":
        return None
    if venda:
        return "importada"
    return "pendente" if lido["problemas"] else "nova"


def _pedidos(conta, status, desde):
    from apps.integrations.services import chamar

    encontrados, offset = [], 0
    while len(encontrados) < LIMITE:
        pagina = chamar(conta, "orders_search", status=status, date_from=desde, offset=offset)
        resultados = pagina.get("results") or []
        encontrados.extend(resultados)
        total = (pagina.get("paging") or {}).get("total") or 0
        offset += len(resultados)
        if not resultados or offset >= total:
            break
    return encontrados


def previa(dias=30):
    """Pedidos pagos e cancelados dos últimos `dias`, com a situação de cada um na loja.
    Só leitura: nada é criado."""
    conta = conta_do_mercado_livre()
    desde = (timezone.now() - timedelta(days=dias)).strftime("%Y-%m-%dT00:00:00.000-03:00")
    vinculos = _vinculos()
    linhas = []
    for status in ("paid", "cancelled"):
        for pedido in _pedidos(conta, status, desde):
            frete = frete_do_vendedor(conta, pedido) if status == "paid" else Decimal("0.00")
            lido = ler_pedido(pedido, vinculos, frete)
            situacao = _situacao(lido)
            if situacao:
                linhas.append({**lido, "situacao": situacao})
    linhas.sort(key=lambda linha: linha["data"], reverse=True)
    return linhas


def importar(order_ids, *, actor):
    """Cria as vendas dos pedidos pagos e cancela as dos pedidos cancelados. Cada pedido é
    buscado de novo no Mercado Livre: os números vêm de lá, não da tela."""
    from apps.integrations.services import chamar
    from apps.sales.services import cancel_sale, create_sale

    conta = conta_do_mercado_livre()
    vinculos = _vinculos()
    resultado = {"importadas": [], "canceladas": [], "ignoradas": [], "falhas": []}
    for order_id in dict.fromkeys(str(o) for o in order_ids):  # sem repetir, na ordem pedida
        try:
            pedido = chamar(conta, "order", order_id=order_id)
            frete = frete_do_vendedor(conta, pedido) if pedido.get("status") == "paid" else Decimal("0.00")
            lido = ler_pedido(pedido, vinculos, frete)
            situacao = _situacao(lido)
            if situacao == "nova":
                with transaction.atomic():
                    agrupado = {}
                    for i in lido["itens"]:
                        linha = agrupado.setdefault(i["produto_id"], {
                            "product_id": uuid.UUID(i["produto_id"]), "quantity": 0, "unit_price": i["preco"],
                        })
                        linha["quantity"] += i["quantidade"]
                    venda = create_sale(data={
                        "idempotency_key": uuid.uuid5(uuid.NAMESPACE_URL, f"jalapao:{CANAL}:{order_id}"),
                        "channel": CANAL,
                        "reference": f"Pedido ML {order_id}"[:100],
                        "discount": Decimal("0.00"),
                        "platform_fee": lido["taxa"],
                        "shipping_cost": lido["frete"] or Decimal("0.00"),
                        "items": list(agrupado.values()),
                    }, actor=actor)
                    venda.external_id = order_id
                    venda.save(update_fields=["external_id", "updated_at"])
                resultado["importadas"].append(order_id)
            elif situacao == "cancelar":
                cancel_sale(sale_id=_venda(order_id).id, actor=actor)
                resultado["canceladas"].append(order_id)
            else:
                motivo = "; ".join(lido["problemas"]) or {
                    "importada": "já importado", None: f"pedido {lido['status'] or 'sem estado'}",
                }.get(situacao, situacao)
                resultado["ignoradas"].append({"order_id": order_id, "motivo": motivo})
        except (IntegrationError, ValidationError) as exc:
            mensagem = "; ".join(exc.messages) if isinstance(exc, ValidationError) else str(exc)
            resultado["falhas"].append({"order_id": order_id, "motivo": mensagem})
    return resultado
