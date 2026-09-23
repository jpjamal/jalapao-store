from django.contrib import admin
from apps.common.admin import LedgerAdmin
from .models import Stock, Movement, Receipt

admin.site.register(Stock, LedgerAdmin)
admin.site.register(Movement, LedgerAdmin)
admin.site.register(Receipt, LedgerAdmin)
