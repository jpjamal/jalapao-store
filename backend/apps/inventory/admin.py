from django.contrib import admin
from apps.common.admin import LedgerAdmin
from .models import Stock, Movement

admin.site.register(Stock, LedgerAdmin)
admin.site.register(Movement, LedgerAdmin)
