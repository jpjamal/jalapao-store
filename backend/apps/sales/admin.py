from django.contrib import admin
from apps.common.admin import LedgerAdmin
from .models import Sale, SaleItem

admin.site.register(Sale, LedgerAdmin)
admin.site.register(SaleItem, LedgerAdmin)
