from django.contrib import admin
from apps.common.admin import LedgerAdmin
from apps.finance.models import CashEntry

admin.site.register(CashEntry, LedgerAdmin)
