import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction


class Command(BaseCommand):
    help = (
        "Cria os usuários autorizados; senha apenas por ambiente, nunca argumento/log. Não reseta existentes."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        password = os.getenv("BOOTSTRAP_PASSWORD")
        if not password:
            raise CommandError("Defina BOOTSTRAP_PASSWORD no ambiente desta execução.")
        for username in ("admin", "jpmorais"):
            user, created = get_user_model().objects.get_or_create(username=username)
            if created:
                user.set_password(password)
                user.is_staff = user.is_superuser = user.is_active = True
                user.save()
            self.stdout.write(f"{username}: {'criado com acesso total' if created else 'preservado'}")
