from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Extension point; native Django groups and model permissions remain authoritative."""
