"""Resultado do negócio (spec 026): o lucro real das vendas mais as entradas e menos as despesas que contam."""

from decimal import Decimal

from django.db.models import Sum

from apps.finance.models import CashEntry


def _total(queryset) -> Decimal:
    return queryset.aggregate(total=Sum("amount"))["total"] or Decimal(0)


def manual_result() -> Decimal:
    """Entradas menos saídas dos lançamentos manuais cujas categorias contam no resultado. As categorias
    do sistema ficam de fora (venda, compra e estoque já estão no lucro real), e empréstimo, aporte e retirada
    do dono não têm a marca, então só mexem no saldo do Caixa."""
    counted = CashEntry.objects.filter(category__system_key__isnull=True, category__counts_in_result=True)
    return _total(counted.filter(direction="in")) - _total(counted.filter(direction="out"))


def supply_expense() -> Decimal:
    """Despesa com insumos: pagamentos de compra menos estornos, só das categorias de insumo com a opção
    "conta como despesa" ligada quando cada compra foi criada. A classificação histórica fica congelada."""
    paid = _total(
        CashEntry.objects.filter(supply_receipt__counts_as_expense_snapshot=True)
    )
    refunded = _total(
        CashEntry.objects.filter(
            refund_of_supply_receipt__counts_as_expense_snapshot=True,
        )
    )
    return paid - refunded


def business_result(realized_profit: Decimal) -> Decimal:
    return Decimal(realized_profit) + manual_result() - supply_expense()


def unclassified_count() -> int:
    """Lançamentos manuais ainda em "A classificar"."""
    return CashEntry.objects.filter(category__system_key="unclassified").count()
