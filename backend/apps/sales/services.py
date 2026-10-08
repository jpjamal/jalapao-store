import hashlib
import json
from decimal import Decimal
from django.db import transaction, connection
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.catalog.models import Product
from apps.common.domain.money import money
from apps.sales.domain.totals import sale_totals
from apps.inventory.services import adjust_stock
from apps.inventory.models import Stock
from apps.inventory.services import outgoing_cost
from apps.finance.models import CashEntry
from apps.sales.models import Sale, SaleItem, SaleRevision
from apps.supplies.services import consume_supplies_for_sale, restore_supplies_for_sale


@transaction.atomic
def create_sale(*, data, actor):
    if connection.vendor == "postgresql":
        lock_key = int.from_bytes(
            hashlib.sha256(str(data["idempotency_key"]).encode()).digest()[:8], "big", signed=True
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [lock_key])
    # The advisory lock serializes this request key without locking the user row.
    # Locking an actor would contend with ledger foreign keys during cancellation.
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
    existing = Sale.objects.filter(idempotency_key=data["idempotency_key"]).first()
    if existing:
        if existing.request_hash != digest or existing.actor_id != actor.id:
            raise ValidationError({"idempotency_key": "Chave já utilizada com outro conteúdo."})
        return existing
    rows = data["items"]
    ids = [row["product_id"] for row in rows]
    if len(set(ids)) != len(ids):
        raise ValidationError({"items": "Agrupe o mesmo produto em uma única linha."})
    products = {p.id: p for p in Product.objects.select_for_update().filter(id__in=ids).order_by("id")}
    if len(products) != len(ids) or any(not p.active for p in products.values()):
        raise ValidationError({"items": "Produto inexistente ou inativo."})
    item_costs = {
        row["product_id"]: outgoing_cost(Stock.objects.get(product_id=row["product_id"]), row["quantity"])
        for row in rows
    }
    costs = sum(item_costs.values(), Decimal(0))
    discount, fee, shipping = (
        data.get(key, Decimal(0)) for key in ("discount", "platform_fee", "shipping_cost")
    )
    totals = sale_totals(items=rows, discount=discount, fee=fee, shipping=shipping)
    gross, net = totals.gross, totals.net
    sale = Sale.objects.create(
        channel=data["channel"],
        reference=data.get("reference", ""),
        idempotency_key=data["idempotency_key"],
        request_hash=digest,
        gross=gross,
        discount=discount,
        platform_fee=fee,
        shipping_cost=shipping,
        cost_total=costs,
        net=net,
        profit=net - costs,
        actor=actor,
    )
    for row in rows:
        product = products[row["product_id"]]
        SaleItem.objects.create(
            sale=sale,
            product=product,
            product_name=product.name,
            quantity=row["quantity"],
            unit_price=row["unit_price"],
            unit_cost=money(item_costs[product.id] / row["quantity"]),
            cost_total=item_costs[product.id],
        )
        adjust_stock(
            product_id=product.id, delta=-row["quantity"], reason="Venda confirmada", actor=actor, sale=sale
        )
    # insumos usados (caixa, etiqueta…): baixa só do que tem, sem mexer no custo nem no lucro
    consume_supplies_for_sale(sale=sale, lines=data.get("supplies") or [], actor=actor)
    return sale


@transaction.atomic
def receive_sale(*, sale_id, actor):
    sale = Sale.objects.select_for_update().get(pk=sale_id)
    if sale.status == "cancelled":
        raise ValidationError({"status": "Venda cancelada não pode ser recebida."})
    if not sale.received_at:
        if sale.net > 0:
            CashEntry.objects.create(
                direction="in",
                amount=sale.net,
                description="Recebimento de venda",
                occurred_on=timezone.localdate(),
                sale=sale,
                actor=actor,
            )
        sale.received_at = timezone.now()
        sale.save(update_fields=["received_at", "updated_at"])
    return sale


@transaction.atomic
def cancel_sale(*, sale_id, actor):
    sale = Sale.objects.select_for_update().get(pk=sale_id)
    if sale.status == "cancelled":
        return sale
    for item in sale.items.order_by("product_id"):
        adjust_stock(
            product_id=item.product_id,
            delta=item.quantity,
            reason="Cancelamento de venda",
            actor=actor,
            sale=sale,
            total_cost=item.cost_total,
        )
    restore_supplies_for_sale(sale=sale, actor=actor)
    if sale.received_at and sale.net > 0:
        CashEntry.objects.create(
            direction="out",
            amount=sale.net,
            description="Estorno de venda",
            occurred_on=timezone.localdate(),
            sale=sale,
            actor=actor,
        )
    sale.status = "cancelled"
    sale.cancelled_at = timezone.now()
    sale.save(update_fields=["status", "cancelled_at", "updated_at"])
    return sale


def _snapshot(sale):
    fields = ("channel", "reference", "external_channel", "external_id", "gross", "discount",
              "platform_fee", "shipping_cost", "net", "profit", "cost_total", "status",
              "received_at", "cancelled_at", "deleted_at")
    result = {name: str(getattr(sale, name)) if getattr(sale, name) is not None else None for name in fields}
    result["items"] = [
        {"id": str(item.id), "product": str(item.product_id), "product_name": item.product_name,
         "quantity": item.quantity, "unit_price": str(item.unit_price), "cost_total": str(item.cost_total)}
        for item in sale.items.order_by("id")
    ]
    return result


@transaction.atomic
def edit_sale(*, sale_id, data, actor):
    sale = Sale.objects.select_for_update().get(pk=sale_id)
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
    previous = sale.revisions.filter(request_key=data["request_key"]).first()
    if previous:
        if previous.request_hash != digest or previous.actor_id != actor.id:
            raise ValidationError({"request_key": "Chave já utilizada com outro conteúdo."})
        return sale
    if sale.status != "confirmed" or sale.deleted_at:
        raise ValidationError({"status": "Venda cancelada ou excluída não pode ser editada."})
    if sale.updated_at != data["expected_updated_at"]:
        raise ValidationError({"version": "Esta venda mudou. Feche e abra a edição para carregar os valores atuais."})
    if sale.received_at and not actor.has_perm("finance.add_cashentry"):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Sem permissão para corrigir o caixa de uma venda recebida.")
    before, old_net = _snapshot(sale), sale.net
    items = list(sale.items.order_by("id"))
    prices = data.get("items", [])
    by_id = {item.id: item for item in items}
    if len({row["id"] for row in prices}) != len(prices) or any(row["id"] not in by_id for row in prices):
        raise ValidationError({"items": "Item repetido ou que não pertence a esta venda."})
    for row in prices:
        by_id[row["id"]].unit_price = row["unit_price"]
    for field in ("channel", "reference", "discount", "platform_fee", "shipping_cost"):
        if field in data:
            setattr(sale, field, data[field])
    totals = sale_totals(
        items=[{"quantity": item.quantity, "unit_price": item.unit_price} for item in items],
        discount=sale.discount, fee=sale.platform_fee, shipping=sale.shipping_cost,
    )
    sale.gross, sale.net, sale.profit = totals.gross, totals.net, totals.net - sale.cost_total
    sale.save(update_fields=["channel", "reference", "discount", "platform_fee", "shipping_cost",
                             "gross", "net", "profit", "updated_at"])
    SaleItem.objects.bulk_update(items, ["unit_price"])
    revision = SaleRevision.objects.create(
        sale=sale, actor=actor, action="edit", before=before, after=_snapshot(sale),
        request_key=data["request_key"], request_hash=digest,
    )
    difference = sale.net - old_net
    if sale.received_at and difference:
        CashEntry.objects.create(
            sale=sale, sale_revision=revision, actor=actor, direction="in" if difference > 0 else "out",
            amount=abs(difference), occurred_on=timezone.localdate(), description="Correção de valor de venda",
        )
    return sale


@transaction.atomic
def delete_sale(*, sale_id, actor):
    sale = Sale.objects.select_for_update().get(pk=sale_id)
    if sale.deleted_at:
        return sale
    before = _snapshot(sale)
    sale = cancel_sale(sale_id=sale.id, actor=actor)
    sale.deleted_at = timezone.now()
    sale.save(update_fields=["deleted_at", "updated_at"])
    SaleRevision.objects.create(sale=sale, actor=actor, action="delete", before=before, after=_snapshot(sale))
    return sale
