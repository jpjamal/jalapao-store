from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Extension point; native Django groups and model permissions remain authoritative."""


class PasswordReset(models.Model):
    """Pedido de senha nova (spec 039). O código só existe no e-mail; o banco guarda o hash."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_resets")
    code_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    invalidated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "created_at"], name="accounts_pwreset_user_created")]
