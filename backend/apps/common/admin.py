from django.contrib import admin


class LedgerAdmin(admin.ModelAdmin):
    """Ledgers are inspected here and changed only through application services."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
