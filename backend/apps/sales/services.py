import hashlib
import json
from decimal import Decimal
from django.db import transaction, connection
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.catalog.models import Product
from apps.catalog.domain import money
from apps.inventory.services import adjust_stock
from apps.finance.models import CashEntry
from .models import Sale, SaleItem


@transaction.atomic
def create_sale(*, data, actor):
    if connection.vendor == "postgresql":
        lock_key = int.from_bytes(
            hashlib.sha256(str(data["idempotency_key"]).encode()).digest()[:8], "big", signed=True
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [lock_key])
    # Serialize repeated submissions by this operator, then lock products in stable order.
    get_user_model().objects.select_for_update().get(pk=actor.pk)
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
    gross = money(sum(row["unit_price"] * row["quantity"] for row in rows))
    costs = money(sum(products[row["product_id"]].cost_price * row["quantity"] for row in rows))
    discount, fee, shipping = (
        data.get(key, Decimal(0)) for key in ("discount", "platform_fee", "shipping_cost")
    )
    net = money(gross - discount - fee - shipping)
    if discount > gross or net < 0:
        raise ValidationError({"discount": "Descontos, taxas e frete não podem superar o valor bruto."})
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
            unit_cost=product.cost_price,
        )
        adjust_stock(
            product_id=product.id, delta=-row["quantity"], reason="Venda confirmada", actor=actor, sale=sale
        )
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
        )
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
