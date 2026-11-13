from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts import services
from apps.common.email import email_configurado


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(trim_whitespace=False)
    password_confirmation = serializers.CharField(trim_whitespace=False)

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirmation"]:
            raise serializers.ValidationError(
                {"password_confirmation": "Digite a mesma senha nos dois campos."}
            )
        return attrs


class MessageSerializer(serializers.Serializer):
    message = serializers.CharField()


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


class _Publica(APIView):
    """Rota sem login (spec 039)."""

    authentication_classes = []
    permission_classes = [AllowAny]


class ResourcesView(_Publica):
    @extend_schema(
        responses=inline_serializer(name="AuthResources", fields={"email_configured": serializers.BooleanField()})
    )
    def get(self, request):
        """Diz se o envio de e-mail está ligado (a tela só mostra "Esqueci minha senha" com ele)."""
        return Response({"email_configured": email_configurado()})


class ForgotPasswordView(_Publica):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "forgot"

    @extend_schema(request=ForgotPasswordSerializer, responses={202: MessageSerializer})
    def post(self, request):
        """Manda o link de senha nova se o e-mail tiver conta; responde igual nos dois casos."""
        entrada = ForgotPasswordSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        services.pedir(entrada.validated_data["email"])
        return Response({"message": "Se esse e-mail tiver conta, enviamos um link."}, status=202)


class ResetPasswordView(_Publica):
    @extend_schema(
        responses={
            200: inline_serializer(name="ResetLinkOk", fields={"email": serializers.CharField()}),
            410: None,
        }
    )
    def get(self, request, code):
        """Diz se o link ainda vale (200, com o e-mail mascarado) ou não (410)."""
        pedido = services.obter(code)
        return Response({"email": services.mascarar_email(pedido.user.email)})

    @extend_schema(request=ResetPasswordSerializer, responses={200: MessageSerializer, 410: None})
    def post(self, request, code):
        """Cria a senha nova pelo link do e-mail e encerra as sessões da pessoa."""
        entrada = ResetPasswordSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        services.redefinir(code, entrada.validated_data["password"])
        return Response({"message": "Senha nova criada. Entre com ela."})
