import hashlib
import json
from django.db import transaction, connection
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.catalog.models import Product
from apps.common.domain.money import money
from apps.inventory.domain.costing import check_value, outgoing_value
from apps.integrations.models import OutboxEvent
from apps.inventory.models import Stock, Movement, Receipt


def outgoing_cost(stock, quantity):
    """Custo das unidades que saem deste estoque (regra em `domain.costing`)."""
    return outgoing_value(available=stock.quantity, value=stock.value, quantity=quantity)


@transaction.atomic
def adjust_stock(
    *, product_id, delta, reason, actor, sale=None, unit_cost=None, total_cost=None, receipt=None,
    restore_value=None,
):
    product = Product.objects.select_for_update().get(pk=product_id)
    stock, _ = Stock.objects.get_or_create(product=product)
    if not delta or not reason.strip():
        raise ValidationError({"reason": "Informe um motivo e uma quantidade diferente de zero."})
    if stock.quantity + delta < 0:
        raise ValidationError(
            {"quantity": f"Estoque insuficiente para {product.name}. Disponível: {stock.quantity}."}
        )
    if stock.quantity + delta > 2147483647:
        raise ValidationError({"quantity": "Quantidade acima do limite suportado."})
    if delta > 0:
        if total_cost is None:
            if unit_cost is None:
                raise ValidationError({"unit_cost": "Informe o custo unitário da entrada."})
            check_value(unit_cost)
            total_cost = money(unit_cost * delta)
        check_value(total_cost)
        value_delta = total_cost
    else:
        if unit_cost is not None:
            raise ValidationError({"unit_cost": "Saídas utilizam automaticamente o custo médio."})
        if restore_value is not None:
            # desfazer uma entrada: tira exatamente o valor que ela pôs, e não o custo médio
            check_value(restore_value)
            value_delta = -restore_value
        else:
            value_delta = -outgoing_cost(stock, -delta)
    check_value(stock.value + value_delta)
    if stock.quantity + delta == 0 and stock.value + value_delta != 0:
        raise ValidationError({"quantity": "O valor do estoque não fecha ao zerar a quantidade."})
    stock.value += value_delta
    stock.quantity += delta
    stock.version += 1
    stock.save(update_fields=["quantity", "version", "value"])
    movement = Movement.objects.create(
        product=product,
        delta=delta,
        balance_after=stock.quantity,
        reason=reason,
        actor=actor,
        sale=sale,
        receipt=receipt,
        value_delta=value_delta,
        value_after=stock.value,
    )
    OutboxEvent.objects.create(
        topic="inventory.changed",
        payload={"product_id": str(product.id), "quantity": stock.quantity, "version": stock.version},
    )
    return movement


@transaction.atomic
def create_receipt(*, data, actor):
    if connection.vendor == "postgresql":
        key = int.from_bytes(
            hashlib.sha256(("receipt:" + str(data["idempotency_key"])).encode()).digest()[:8],
            "big",
            signed=True,
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [key])
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
    existing = Receipt.objects.filter(idempotency_key=data["idempotency_key"]).first()
    if existing:
        if existing.request_hash != digest or existing.actor_id != actor.id:
            raise ValidationError({"idempotency_key": "Chave já utilizada com outro conteúdo."})
        return existing
    product = Product.objects.select_for_update().filter(pk=data["product_id"], active=True).first()
    if not product:
        raise ValidationError({"product_id": "Produto inexistente ou inativo."})
    if data["quantity"] <= 0:
        raise ValidationError({"quantity": "Informe uma quantidade positiva."})
    check_value(data["unit_cost"])
    total = money(data["unit_cost"] * data["quantity"])
    check_value(total)
    receipt = Receipt.objects.create(
        **data, product_name=product.name, total=total, request_hash=digest, actor=actor
    )
    adjust_stock(
        product_id=product.id,
        delta=receipt.quantity,
        total_cost=total,
        reason=f"{receipt.get_kind_display()}: {receipt.reference or 'entrada de estoque'}",
        actor=actor,
        receipt=receipt,
    )
    return receipt


@transaction.atomic
def pay_receipt(*, receipt_id, occurred_on, actor):
    from apps.finance.models import CashEntry

    receipt = Receipt.objects.select_for_update().get(pk=receipt_id)
    if receipt.status == Receipt.Status.CANCELLED:
        raise ValidationError({"status": "Compra cancelada não pode ser paga."})
    if receipt.kind != Receipt.Kind.PURCHASE:
        raise ValidationError(
            {"kind": "Produção não gera pagamento automático. Registre despesas efetivamente pagas no caixa."}
        )
    if occurred_on > timezone.localdate():
        raise ValidationError({"occurred_on": "Pagamento não pode ter data futura."})
    if not receipt.paid_at:
        if receipt.total > 0:
            CashEntry.objects.create(
                direction="out",
                amount=receipt.total,
                receipt=receipt,
                occurred_on=occurred_on,
                actor=actor,
                description=f"Compra: {receipt.product_name}"[:240],
            )
        receipt.paid_at = timezone.now()
        receipt.save(update_fields=["paid_at", "updated_at"])
    return receipt


@transaction.atomic
def cancel_receipt(*, receipt_id, actor):
    """Cancela uma compra ou produção lançada errada, sem apagar nada (spec 023).

    Só vale enquanto a entrada for a última movimentação do produto: assim tirar as unidades e
    o valor dela devolve o estoque exatamente ao que era antes, sem mexer no custo médio de
    outras entradas. Compra já paga gera um estorno de entrada no caixa."""
    from apps.finance.models import CashEntry

    receipt = Receipt.objects.select_for_update().get(pk=receipt_id)
    if receipt.status == Receipt.Status.CANCELLED:
        return receipt
    Product.objects.select_for_update().get(pk=receipt.product_id)
    entry = Movement.objects.filter(receipt=receipt).first()
    later = (
        Movement.objects.filter(product_id=receipt.product_id, created_at__gte=entry.created_at)
        .exclude(pk=entry.pk)
        .exists()
        if entry
        else True
    )
    if later:
        raise ValidationError(
            {
                "receipt": "Este produto teve outras movimentações depois desta entrada (venda, ajuste ou "
                "outra entrada), então ela não pode ser cancelada sem distorcer o custo. "
                "Corrija pelos ajustes de estoque."
            }
        )
    adjust_stock(
        product_id=receipt.product_id,
        delta=-receipt.quantity,
        reason=f"Cancelamento de {receipt.get_kind_display().lower()}: {receipt.reference or 'entrada de estoque'}",
        actor=actor,
        restore_value=receipt.total,
    )
    if receipt.paid_at and receipt.total > 0:
        CashEntry.objects.create(
            direction="in",
            amount=receipt.total,
            description=f"Estorno de compra: {receipt.product_name}"[:240],
            occurred_on=timezone.localdate(),
            refund_of_receipt=receipt,
            actor=actor,
        )
    receipt.status = Receipt.Status.CANCELLED
    receipt.cancelled_at = timezone.now()
    receipt.save(update_fields=["status", "cancelled_at", "updated_at"])
    return receipt
