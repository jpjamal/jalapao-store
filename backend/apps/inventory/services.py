from django.db import transaction
from django.core.exceptions import ValidationError
from apps.catalog.models import Product
from apps.integrations.models import OutboxEvent
from .models import Stock, Movement


@transaction.atomic
def adjust_stock(*, product_id, delta, reason, actor, sale=None):
    product = Product.objects.select_for_update().get(pk=product_id)
    stock, _ = Stock.objects.get_or_create(product=product)
    if not delta or not reason.strip():
        raise ValidationError({"reason": "Informe um motivo e uma quantidade diferente de zero."})
    if stock.quantity + delta < 0:
        raise ValidationError(
            {"quantity": f"Estoque insuficiente para {product.name}. Disponível: {stock.quantity}."}
        )
    stock.quantity += delta
    stock.version += 1
    stock.save(update_fields=["quantity", "version"])
    movement = Movement.objects.create(
        product=product, delta=delta, balance_after=stock.quantity, reason=reason, actor=actor, sale=sale
    )
    OutboxEvent.objects.create(
        topic="inventory.changed",
        payload={"product_id": str(product.id), "quantity": stock.quantity, "version": stock.version},
    )
    return movement
