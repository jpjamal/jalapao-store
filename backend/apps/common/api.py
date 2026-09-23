from decimal import Decimal
from django.db import connection
from django.db.models import Sum, F, DecimalField
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, inline_serializer
from apps.catalog.models import Product
from apps.sales.models import Sale
from apps.finance.models import CashEntry


def health(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return JsonResponse({"ok": True})


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses=inline_serializer(
            name="Dashboard",
            fields={
                **{
                    key: serializers.CharField()
                    for key in ("stock_value", "gross", "profit", "receivable", "cash_balance")
                },
                "product_count": serializers.IntegerField(),
            },
        )
    )
    def get(self, request):
        if not request.user.has_perms(["catalog.view_product", "sales.view_sale", "finance.view_cashentry"]):
            raise PermissionDenied()
        sales = Sale.objects.filter(status="confirmed")
        totals = sales.aggregate(gross=Sum("gross"), profit=Sum("profit"))
        stock = (
            Product.objects.aggregate(
                value=Sum(F("stock__quantity") * F("cost_price"), output_field=DecimalField())
            )["value"]
            or 0
        )
        cash = dict(CashEntry.objects.values_list("direction").annotate(total=Sum("amount")))
        return Response(
            {
                "stock_value": str(stock),
                "gross": str(totals["gross"] or 0),
                "profit": str(totals["profit"] or 0),
                "receivable": str(
                    sales.filter(received_at__isnull=True).aggregate(total=Sum("net"))["total"] or 0
                ),
                "cash_balance": str(cash.get("in", Decimal(0)) - cash.get("out", Decimal(0))),
                "product_count": Product.objects.filter(active=True).count(),
            }
        )
