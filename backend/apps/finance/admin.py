from django.contrib import admin
from apps.common.admin import LedgerAdmin
from .models import CashEntry

admin.site.register(CashEntry, LedgerAdmin)
