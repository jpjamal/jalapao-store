from django.contrib import admin

from apps.common.admin import LedgerAdmin
from apps.supplies.models import Supply, SupplyCategory, SupplyMovement, SupplyReceipt, SupplyStock


@admin.register(SupplyCategory)
class SupplyCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "is_filament", "counts_as_expense", "active"]
    list_filter = ["is_filament", "counts_as_expense", "active"]
    search_fields = ["name"]


@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "unit", "material", "color", "roll_price", "active"]
    list_filter = ["category", "active"]
    search_fields = ["name", "color", "material"]


admin.site.register(SupplyStock, LedgerAdmin)
admin.site.register(SupplyReceipt, LedgerAdmin)
admin.site.register(SupplyMovement, LedgerAdmin)
