from django.contrib import admin
from .models import Product, PrintingProfile


class PrintingInline(admin.StackedInline):
    model = PrintingProfile
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["sku", "name", "kind", "cost_price", "sale_price", "active"]
    list_filter = ["kind", "active"]
    search_fields = ["sku", "name"]
    inlines = [PrintingInline]
    readonly_fields = ["sku"]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        from apps.inventory.models import Stock

        Stock.objects.get_or_create(product=form.instance)
        if form.instance.kind == "printing" and hasattr(form.instance, "printing"):
            form.instance.cost_price, form.instance.sale_price = form.instance.printing.prices()
            form.instance.save()
