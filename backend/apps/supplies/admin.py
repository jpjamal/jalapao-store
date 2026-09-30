from django.contrib import admin

from apps.supplies.models import Supply, SupplyCategory, SupplyMovement, SupplyReceipt, SupplyStock


@admin.register(SupplyCategory)
class SupplyCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "is_filament", "active"]
    list_filter = ["is_filament", "active"]
    search_fields = ["name"]


@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "unit", "material", "color", "roll_price", "active"]
    list_filter = ["category", "active"]
    search_fields = ["name", "color", "material"]


class LedgerAdmin(admin.ModelAdmin):
    """Só leitura: o saldo e o histórico mudam pelos serviços, nunca à mão no Admin."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(SupplyStock, LedgerAdmin)
admin.site.register(SupplyReceipt, LedgerAdmin)
admin.site.register(SupplyMovement, LedgerAdmin)
