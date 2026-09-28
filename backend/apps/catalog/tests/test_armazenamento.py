"""Migração das fotos do disco para o armazenamento configurado (spec 020).

O armazenamento de destino aqui é outra pasta: o comando só usa a API de Storage, então o que
vale para o disco vale para o bucket. O bucket de verdade foi conferido no ensaio com o SILO."""

from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from apps.catalog.models import Product, ProductImage


class MediaStorageTests(TestCase):
    def setUp(self):
        self.old_disk = Path(self.enterContext(TemporaryDirectory()))
        self.enterContext(override_settings(MEDIA_ROOT=self.enterContext(TemporaryDirectory())))
        self.product = Product.objects.create(name="Luminária Pimentão")

    def photo(self, name, content=b"foto", on_disk=True):
        if on_disk:
            path = self.old_disk / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        return ProductImage.objects.create(
            product=self.product, file=name, mime_type="image/png", width=1, height=1, size_bytes=len(content)
        )

    def migrate(self):
        out, err = StringIO(), StringIO()
        call_command("migrate_media_to_storage", str(self.old_disk), stdout=out, stderr=err)
        return out.getvalue(), err.getvalue()

    def test_copies_with_same_name_and_is_idempotent(self):
        image = self.photo(f"products/{self.product.pk}/a.png", b"conteudo-a")
        out, _ = self.migrate()
        self.assertIn("1 copiadas, 0 já estavam lá, 0 sem arquivo", out)
        with image.file.open("rb") as handle:
            self.assertEqual(handle.read(), b"conteudo-a")
        out, _ = self.migrate()
        self.assertIn("0 copiadas, 1 já estavam lá", out)
        self.assertTrue((self.old_disk / image.file.name).exists(), "o disco antigo não pode ser alterado")

    def test_reports_photo_without_file_and_keeps_going(self):
        self.photo(f"products/{self.product.pk}/sumiu.png", on_disk=False)
        self.photo(f"products/{self.product.pk}/b.png")
        out, err = self.migrate()
        self.assertIn("1 copiadas, 0 já estavam lá, 1 sem arquivo", out)
        self.assertIn("sumiu.png", err)

    def test_missing_source_folder_is_an_error(self):
        with self.assertRaises(CommandError):
            call_command("migrate_media_to_storage", str(self.old_disk / "nao-existe"))
