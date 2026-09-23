from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers


class LoginView(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses=inline_serializer(
            name="CurrentUser",
            fields={
                "username": serializers.CharField(),
                "is_superuser": serializers.BooleanField(),
                "permissions": serializers.ListField(child=serializers.CharField()),
            },
        )
    )
    def get(self, request):
        return Response(
            {
                "username": request.user.username,
                "is_superuser": request.user.is_superuser,
                "permissions": sorted(request.user.get_all_permissions()),
            }
        )
