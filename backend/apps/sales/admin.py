from django.contrib import admin
from apps.common.admin import LedgerAdmin
from apps.sales.models import Sale, SaleItem, SaleRevision

admin.site.register(Sale, LedgerAdmin)
admin.site.register(SaleItem, LedgerAdmin)
admin.site.register(SaleRevision, LedgerAdmin)
