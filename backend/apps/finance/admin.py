from django.contrib import admin
from apps.common.admin import LedgerAdmin
from apps.finance.models import CashCategory, CashEntry


@admin.register(CashCategory)
class CashCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "direction", "counts_in_result", "active", "system_key"]
    list_filter = ["direction", "counts_in_result", "active"]
    search_fields = ["name"]
    readonly_fields = ["system_key"]


admin.site.register(CashEntry, LedgerAdmin)
