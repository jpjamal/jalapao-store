"""Casos de uso do estoque de insumos (spec 024, etapa 2). Toda escrita de saldo passa por
`adjust_supply_stock`; compra, pagamento e cancelamento reaproveitam o mesmo molde das entradas de
produto, sem custo médio: o estoque de insumo guarda só a quantidade."""

import hashlib
import json

from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.utils import timezone

from apps.common.domain.money import money
from apps.supplies.domain.pricing import check_amount
from apps.supplies.models import Supply, SupplyMovement, SupplyReceipt, SupplyStock

LIMITE_QUANTIDADE = 2147483647


@transaction.atomic
def adjust_supply_stock(*, supply_id, delta, reason, actor, receipt=None, sale=None):
    """Muda o saldo de um insumo e grava o movimento. Nunca deixa o saldo negativo."""
    supply = Supply.objects.select_for_update().get(pk=supply_id)
    stock, _ = SupplyStock.objects.get_or_create(supply=supply)
    if not delta or not (reason or "").strip():
        raise ValidationError({"reason": "Informe um motivo e uma quantidade diferente de zero."})
    if delta > 0 and not supply.active:
        raise ValidationError({"supply": f"O insumo {supply.name} está inativo e não recebe entradas."})
    if stock.quantity + delta < 0:
        raise ValidationError(
            {"quantity": f"Saldo insuficiente de {supply.name}. Disponível: {stock.quantity}."}
        )
    if stock.quantity + delta > LIMITE_QUANTIDADE:
        raise ValidationError({"quantity": "Quantidade acima do limite suportado."})
    stock.quantity += delta
    stock.version += 1
    stock.save(update_fields=["quantity", "version"])
    return SupplyMovement.objects.create(
        supply=supply,
        delta=delta,
        balance_after=stock.quantity,
        reason=reason.strip(),
        actor=actor,
        receipt=receipt,
        sale=sale,
    )


@transaction.atomic
def create_supply_receipt(*, data, actor):
    """Registra a compra de um insumo: entra no saldo na hora e fica a pagar. Compra de filamento
    atualiza o preço do rolo do cadastro para o custo unitário (o último preço pago)."""
    if connection.vendor == "postgresql":
        key = int.from_bytes(
            hashlib.sha256(("supply-receipt:" + str(data["idempotency_key"])).encode()).digest()[:8],
            "big",
            signed=True,
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [key])
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
    existing = SupplyReceipt.objects.filter(idempotency_key=data["idempotency_key"]).first()
    if existing:
        if existing.request_hash != digest or existing.actor_id != actor.id:
            raise ValidationError({"idempotency_key": "Chave já utilizada com outro conteúdo."})
        return existing
    supply = (
        Supply.objects.select_for_update()
        .select_related("category")
        .filter(pk=data["supply_id"], active=True)
        .first()
    )
    if not supply:
        raise ValidationError({"supply_id": "Insumo inexistente ou inativo."})
    if data["quantity"] <= 0:
        raise ValidationError({"quantity": "Informe uma quantidade positiva."})
    check_amount(data["unit_cost"])
    total = money(data["unit_cost"] * data["quantity"])
    check_amount(total)
    fields = {k: v for k, v in data.items() if k != "supply_id"}
    receipt = SupplyReceipt.objects.create(
        **fields,
        supply=supply,
        supply_name=supply.name,
        total=total,
        request_hash=digest,
        previous_roll_price=supply.roll_price if supply.category.is_filament else None,
        actor=actor,
    )
    adjust_supply_stock(
        supply_id=supply.id,
        delta=receipt.quantity,
        reason=f"Compra de insumo: {receipt.reference or 'entrada de estoque'}",
        actor=actor,
        receipt=receipt,
    )
    if supply.category.is_filament:
        supply.roll_price = money(data["unit_cost"])
        supply.save(update_fields=["roll_price", "updated_at"])
    return receipt


@transaction.atomic
def pay_supply_receipt(*, receipt_id, occurred_on, actor):
    """Paga a compra: uma única saída no caixa com o total, na data informada."""
    from apps.finance.models import CashEntry

    receipt = SupplyReceipt.objects.select_for_update().get(pk=receipt_id)
    if receipt.status == SupplyReceipt.Status.CANCELLED:
        raise ValidationError({"status": "Compra cancelada não pode ser paga."})
    if occurred_on > timezone.localdate():
        raise ValidationError({"occurred_on": "Pagamento não pode ter data futura."})
    if not receipt.paid_at:
        if receipt.total > 0:
            CashEntry.objects.create(
                direction="out",
                amount=receipt.total,
                supply_receipt=receipt,
                occurred_on=occurred_on,
                actor=actor,
                description=f"Insumo: {receipt.supply_name}"[:240],
            )
        receipt.paid_at = timezone.now()
        receipt.save(update_fields=["paid_at", "updated_at"])
    return receipt


@transaction.atomic
def cancel_supply_receipt(*, receipt_id, actor):
    """Cancela uma compra de insumo lançada errada, sem apagar nada. Só vale enquanto ela for a
    última movimentação do insumo; compra paga gera um estorno de entrada no caixa."""
    from apps.finance.models import CashEntry

    receipt = SupplyReceipt.objects.select_for_update().get(pk=receipt_id)
    if receipt.status == SupplyReceipt.Status.CANCELLED:
        return receipt
    supply = Supply.objects.select_for_update().get(pk=receipt.supply_id)
    entry = SupplyMovement.objects.filter(receipt=receipt).first()
    later = (
        SupplyMovement.objects.filter(supply_id=supply.pk, created_at__gte=entry.created_at)
        .exclude(pk=entry.pk)
        .exists()
        if entry
        else True
    )
    if later:
        raise ValidationError(
            {
                "receipt": "Este insumo teve outras movimentações depois desta compra (baixa, ajuste ou "
                "outra compra), então ela não pode ser cancelada. Corrija pelos ajustes de estoque."
            }
        )
    adjust_supply_stock(
        supply_id=supply.pk,
        delta=-receipt.quantity,
        reason=f"Cancelamento de compra de insumo: {receipt.reference or 'entrada de estoque'}",
        actor=actor,
    )
    if receipt.paid_at and receipt.total > 0:
        CashEntry.objects.create(
            direction="in",
            amount=receipt.total,
            description=f"Estorno de compra de insumo: {receipt.supply_name}"[:240],
            occurred_on=timezone.localdate(),
            refund_of_supply_receipt=receipt,
            actor=actor,
        )
    # o preço do rolo volta ao de antes só se ainda for o da compra (o dono pode tê-lo editado)
    if receipt.previous_roll_price is not None and supply.roll_price == money(receipt.unit_cost):
        supply.roll_price = receipt.previous_roll_price
        supply.save(update_fields=["roll_price", "updated_at"])
    receipt.status = SupplyReceipt.Status.CANCELLED
    receipt.cancelled_at = timezone.now()
    receipt.save(update_fields=["status", "cancelled_at", "updated_at"])
    return receipt
