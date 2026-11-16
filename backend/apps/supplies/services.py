"""Casos de uso do estoque de insumos (spec 024, etapa 2). Toda escrita de saldo passa por
`adjust_supply_stock`; compra, pagamento e cancelamento reaproveitam o mesmo molde das entradas de
produto, sem custo médio: o estoque de insumo guarda só a quantidade.

Custo na venda (spec 040): cada insumo tem um custo unitário (o da última compra ou do último ajuste de
entrada com custo) e o saldo tem uma parte **sem custo** (`SupplyStock.uncosted`): unidades cuja compra
já entrou como despesa no Resultado do negócio, entradas sem custo e o saldo anterior à spec 040. Toda
saída consome a parte sem custo primeiro. Assim o mesmo custo nunca conta duas vezes."""

import hashlib
import json

from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.utils import timezone

from apps.common.domain.money import money
from apps.supplies.domain.pricing import check_amount
from apps.supplies.models import ProductSupply, SaleSupply, Supply, SupplyMovement, SupplyReceipt, SupplyStock

LIMITE_QUANTIDADE = 2147483647


@transaction.atomic
def adjust_supply_stock(
    *, supply_id, delta, reason, actor, receipt=None, sale=None, allow_inactive=False, uncosted=None,
    unit_cost=None,
):
    """Muda o saldo de um insumo e grava o movimento. Nunca deixa o saldo negativo.

    `uncosted` é quanto muda a parte sem custo do saldo. Sem ele, entrada é sem custo e saída consome a
    parte sem custo primeiro."""
    supply = Supply.objects.select_for_update().get(pk=supply_id)
    stock, _ = SupplyStock.objects.get_or_create(supply=supply)
    if not delta or not (reason or "").strip():
        raise ValidationError({"reason": "Informe um motivo e uma quantidade diferente de zero."})
    if delta > 0 and not supply.active and not allow_inactive:
        raise ValidationError({"supply": f"O insumo {supply.name} está inativo e não recebe entradas."})
    if stock.quantity + delta < 0:
        raise ValidationError(
            {"quantity": f"Saldo insuficiente de {supply.name}. Disponível: {stock.quantity}."}
        )
    if stock.quantity + delta > LIMITE_QUANTIDADE:
        raise ValidationError({"quantity": "Quantidade acima do limite suportado."})
    if uncosted is None:
        uncosted = delta if delta > 0 else -min(stock.uncosted, -delta)
    stock.quantity += delta
    # a parte sem custo nunca passa do saldo nem fica negativa
    stock.uncosted = max(0, min(stock.quantity, stock.uncosted + uncosted))
    stock.version += 1
    stock.save(update_fields=["quantity", "uncosted", "version"])
    return SupplyMovement.objects.create(
        supply=supply,
        delta=delta,
        balance_after=stock.quantity,
        reason=reason.strip(),
        unit_cost=unit_cost,
        actor=actor,
        receipt=receipt,
        sale=sale,
    )


@transaction.atomic
def register_supply_adjustment(*, supply_id, delta, reason, actor, unit_cost=None):
    """Baixa ou ajuste feito à mão (spec 024). Ajuste de **entrada com custo unitário** (spec 040), por
    exemplo embalagens que já estavam em casa: entra com esse custo nas vendas e vira o custo do insumo,
    sem tocar no caixa. Sem custo, a entrada sai nas vendas sem custo."""
    if unit_cost is not None and delta <= 0:
        raise ValidationError({"unit_cost": "Custo unitário só vale para entrada (quantidade positiva)."})
    if unit_cost is not None:
        check_amount(unit_cost)
    movement = adjust_supply_stock(
        supply_id=supply_id,
        delta=delta,
        reason=reason,
        actor=actor,
        uncosted=0 if unit_cost is not None else None,
        unit_cost=money(unit_cost) if unit_cost is not None else None,
    )
    if unit_cost is not None:
        Supply.objects.filter(pk=supply_id).update(unit_cost=money(unit_cost), updated_at=timezone.now())
    return movement


@transaction.atomic
def create_supply_receipt(*, data, actor):
    """Registra a compra de um insumo: entra no saldo na hora e fica a pagar. O custo unitário da compra
    vira o custo do insumo nas vendas (o último preço pago); no filamento, também o preço do rolo."""
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
        counts_as_expense_snapshot=supply.category.counts_as_expense,
        request_hash=digest,
        previous_roll_price=supply.roll_price if supply.category.is_filament else None,
        previous_unit_cost=supply.unit_cost,
        actor=actor,
    )
    # compra que já conta como despesa no Resultado do negócio entra sem custo para as vendas (spec 040)
    adjust_supply_stock(
        supply_id=supply.id,
        delta=receipt.quantity,
        reason=f"Compra de insumo: {receipt.reference or 'entrada de estoque'}",
        actor=actor,
        receipt=receipt,
        uncosted=receipt.quantity if receipt.counts_as_expense_snapshot else 0,
    )
    supply.unit_cost = money(data["unit_cost"])
    update = ["unit_cost", "updated_at"]
    if supply.category.is_filament:
        supply.roll_price = money(data["unit_cost"])
        update.append("roll_price")
    supply.save(update_fields=update)
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
        uncosted=-receipt.quantity if receipt.counts_as_expense_snapshot else 0,
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
    supply.refresh_from_db()
    update = []
    # o preço do rolo volta ao de antes só se ainda for o da compra (o dono pode tê-lo editado)
    if receipt.previous_roll_price is not None and supply.roll_price == money(receipt.unit_cost):
        supply.roll_price = receipt.previous_roll_price
        update.append("roll_price")
    # o custo unitário também volta ao de antes, se ainda for o desta compra (spec 040)
    if supply.unit_cost == money(receipt.unit_cost):
        supply.unit_cost = receipt.previous_unit_cost
        update.append("unit_cost")
    if update:
        supply.save(update_fields=[*update, "updated_at"])
    receipt.status = SupplyReceipt.Status.CANCELLED
    receipt.cancelled_at = timezone.now()
    receipt.save(update_fields=["status", "cancelled_at", "updated_at"])
    return receipt


@transaction.atomic
def consume_supplies_for_sale(*, sale, lines, actor):
    """Dá baixa nos insumos usados numa venda, na mesma transação dela (spec 024, etapa 3).

    Saldo insuficiente não impede a venda: o insumo é baixado só até onde tem, e o que foi pedido e o
    que foi baixado ficam gravados em `SaleSupply`, para a tela avisar o que faltou.

    Custo (spec 040): a parte sem custo do saldo sai primeiro, a custo zero; o resto sai pelo custo
    unitário do insumo. Filamento sai sempre a custo zero (o custo dele já está no custo da peça). O custo
    fica congelado na linha; quem chama soma e desconta do lucro da venda."""
    if not lines:
        return []
    ids = [line["supply_id"] for line in lines]
    if len(set(ids)) != len(ids):
        raise ValidationError({"supplies": "Agrupe o mesmo insumo em uma única linha."})
    supplies = {
        s.id: s
        for s in Supply.objects.select_for_update(of=("self",)).select_related("category").filter(id__in=ids).order_by("id")
    }
    if len(supplies) != len(ids):
        raise ValidationError({"supplies": "Insumo inexistente."})
    used = []
    for line in sorted(lines, key=lambda row: str(row["supply_id"])):
        supply = supplies[line["supply_id"]]
        stock, _ = SupplyStock.objects.get_or_create(supply=supply)
        requested = line["quantity"]
        taken = min(requested, stock.quantity)
        zero_cost = min(stock.uncosted, taken)
        if taken > 0:
            adjust_supply_stock(
                supply_id=supply.id, delta=-taken, reason="Venda confirmada", actor=actor, sale=sale,
                uncosted=-zero_cost,
            )
        if supply.category.is_filament:
            zero_cost, unit_cost = taken, money(0)
        else:
            unit_cost = money(supply.unit_cost or 0)
        used.append(
            SaleSupply.objects.create(
                sale=sale,
                supply=supply,
                supply_name=supply.name,
                requested=requested,
                taken=taken,
                zero_cost_qty=zero_cost,
                unit_cost=unit_cost,
                cost_total=money(unit_cost * (taken - zero_cost)),
            )
        )
    return used


@transaction.atomic
def restore_supplies_for_sale(*, sale, actor):
    """Devolve ao saldo o que a venda baixou (só `taken`), mesmo que o insumo esteja inativo hoje. O que
    saiu sem custo volta sem custo; o resto volta com custo (spec 040)."""
    for line in SaleSupply.objects.select_for_update().filter(sale=sale, taken__gt=0).order_by("supply_id"):
        adjust_supply_stock(
            supply_id=line.supply_id,
            delta=line.taken,
            reason="Cancelamento de venda",
            actor=actor,
            sale=sale,
            allow_inactive=True,
            uncosted=line.zero_cost_qty,
        )


@transaction.atomic
def set_product_supplies(*, product, lines):
    """Troca a embalagem padrão do produto (spec 040) pelas linhas informadas."""
    ids = [line["supply"].id for line in lines]
    if len(set(ids)) != len(ids):
        raise ValidationError({"default_supplies": "Agrupe o mesmo insumo em uma única linha."})
    ProductSupply.objects.filter(product=product).exclude(supply_id__in=ids).delete()
    for line in lines:
        ProductSupply.objects.update_or_create(
            product=product, supply=line["supply"], defaults={"quantity": line["quantity"]}
        )
