"""Preenche o e-mail do usuário `jpmorais` quando ele está em branco (spec 039).

O endereço vem da variável de ambiente JPMORAIS_EMAIL (variável do GitHub, nunca o repositório
público). Idempotente: sem a variável, ou com o e-mail já preenchido, não muda nada.
"""

import os

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.core.validators import validate_email


class Command(BaseCommand):
    help = "Preenche o e-mail do jpmorais se estiver em branco (lê JPMORAIS_EMAIL)."

    def handle(self, *args, **options):
        email = os.getenv("JPMORAIS_EMAIL", "").strip()
        if not email:
            self.stdout.write("JPMORAIS_EMAIL não definido: nada a fazer.")
            return
        try:
            validate_email(email)
        except ValidationError:
            self.stderr.write("JPMORAIS_EMAIL não é um e-mail válido: nada foi alterado.")
            return
        usuario = get_user_model().objects.filter(username="jpmorais").first()
        if usuario is None:
            self.stdout.write("Usuário jpmorais não existe: nada a fazer.")
        elif usuario.email:
            self.stdout.write("jpmorais já tem e-mail: preservado.")
        else:
            usuario.email = email
            usuario.save(update_fields=["email"])
            self.stdout.write("jpmorais: e-mail cadastrado.")
