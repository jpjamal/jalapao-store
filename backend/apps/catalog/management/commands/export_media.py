import sys
import tarfile

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from apps.catalog.models import ProductImage


class Command(BaseCommand):
    help = (
        "Escreve na saída padrão um .tar.gz com as fotos dos produtos, lidas do armazenamento "
        "configurado (disco ou bucket). É o backup de fotos do deploy, feito junto com o do banco."
    )

    def handle(self, *args, **options):
        missing = 0
        with tarfile.open(fileobj=sys.stdout.buffer, mode="w|gz") as archive:
            for name in ProductImage.objects.values_list("file", flat=True).order_by("file"):
                try:
                    handle = default_storage.open(name, "rb")
                except FileNotFoundError:
                    missing += 1
                    self.stderr.write(f"Foto sem arquivo no armazenamento: {name}")
                    continue
                with handle:
                    info = tarfile.TarInfo(f"media/{name}")
                    info.size = handle.size
                    info.mtime = default_storage.get_modified_time(name).timestamp()
                    archive.addfile(info, handle)
        if missing:
            self.stderr.write(f"{missing} foto(s) ficaram fora do backup por falta de arquivo.")
