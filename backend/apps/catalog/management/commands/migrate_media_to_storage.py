from pathlib import Path

from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError

from apps.catalog.models import ProductImage


class Command(BaseCommand):
    help = (
        "Copia as fotos dos produtos de uma pasta do disco para o armazenamento configurado (o bucket "
        "do servidor de arquivos), com o mesmo nome. Idempotente: o que já está lá não é tocado, e o "
        "disco nunca é alterado (spec 020)."
    )

    def add_arguments(self, parser):
        parser.add_argument("source", help="pasta antiga das fotos (o MEDIA_ROOT de antes)")

    def handle(self, *args, **options):
        source = Path(options["source"])
        if not source.is_dir():
            raise CommandError(f"A pasta {source} não existe.")
        copied = present = 0
        missing = []
        for name in ProductImage.objects.values_list("file", flat=True).order_by("file"):
            if default_storage.exists(name):
                present += 1
                continue
            path = source / name
            if not path.is_file():
                missing.append(name)
                continue
            with path.open("rb") as handle:
                saved = default_storage.save(name, File(handle, name=path.name))
            if saved != name:
                raise CommandError(f"O armazenamento gravou {saved} no lugar de {name}; migração interrompida.")
            copied += 1
        for name in missing:
            self.stderr.write(f"Sem arquivo no disco nem no armazenamento: {name}")
        self.stdout.write(f"Fotos: {copied} copiadas, {present} já estavam lá, {len(missing)} sem arquivo.")
