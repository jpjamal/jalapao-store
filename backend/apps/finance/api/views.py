from rest_framework import mixins, viewsets

from apps.finance.api.serializers import CashSerializer
from apps.finance.models import CashEntry


class CashViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = CashEntry.objects.all()
    serializer_class = CashSerializer
    filterset_fields = ["direction"]
