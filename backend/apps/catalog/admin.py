from django.contrib import admin
from apps.catalog.models import Category, Product, PrintingProfile


class PrintingInline(admin.StackedInline):
    model = PrintingProfile
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "uses_printing_profile", "active"]
    list_filter = ["uses_printing_profile", "active"]
    search_fields = ["name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["sku", "gtin", "name", "category", "cost_price", "sale_price", "active"]
    list_filter = ["category", "active"]
    search_fields = ["sku", "gtin", "name", "brand", "model"]
    inlines = [PrintingInline]
    readonly_fields = ["sku"]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        from apps.inventory.models import Stock

        Stock.objects.get_or_create(product=form.instance)
        if form.instance.category.uses_printing_profile and hasattr(form.instance, "printing"):
            form.instance.cost_price, form.instance.sale_price = form.instance.printing.prices()
            form.instance.save()
