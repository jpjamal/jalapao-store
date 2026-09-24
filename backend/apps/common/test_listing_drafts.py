from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from apps.catalog.models import ListingDraft, Product, ProductImage
from apps.integrations.models import Listing


def png_file(name="photo.png"):
    image = Image.new("RGB", (40, 40), "#ffffff")
    data = BytesIO()
    image.save(data, format="PNG")
    data.seek(0)
    from django.core.files.uploadedfile import SimpleUploadedFile

    return SimpleUploadedFile(name, data.read(), content_type="image/png")


class ListingDraftTests(TestCase):
    def setUp(self):
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.media.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.client = APIClient()
        self.client.force_authenticate(get_user_model().objects.create_superuser("draft-admin", password="test-pass"))
        self.product = Product.objects.create(name="Luminária Pimentão")
        self.other = Product.objects.create(name="Outro produto")

    def upload(self, product=None):
        response = self.client.post(
            "/api/v1/product-images/",
            {"product": str((product or self.product).pk), "file": png_file()},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()["id"]

    def test_drafts_are_separate_by_channel_and_never_create_remote_listing(self):
        image_id = self.upload()
        base = {"product": str(self.product.pk), "image_ids": [image_id]}
        ml = self.client.post(
            "/api/v1/listing-drafts/",
            {**base, "channel": "mercado_livre", "title": "Título ML", "price": "69.76"},
            format="json",
        )
        shopee = self.client.post(
            "/api/v1/listing-drafts/",
            {**base, "channel": "shopee", "title": "Título Shopee", "price": "74.90"},
            format="json",
        )
        self.assertEqual((ml.status_code, shopee.status_code), (201, 201))
        self.assertEqual(ml.json()["image_ids"], [image_id])
        self.assertEqual(shopee.json()["image_ids"], [image_id])
        self.assertEqual(ListingDraft.objects.count(), 2)
        self.assertFalse(Listing.objects.exists())
        self.assertEqual(self.product.sku, Product.objects.get(pk=self.product.pk).sku)
        changed = self.client.patch(
            f"/api/v1/listing-drafts/{ml.json()['id']}/", {"title": "Novo título ML"}, format="json"
        )
        self.assertEqual(changed.status_code, 200)
        self.assertEqual(ListingDraft.objects.get(pk=shopee.json()["id"]).title, "Título Shopee")
        duplicate = self.client.post(
            "/api/v1/listing-drafts/", {**base, "channel": "mercado_livre"}, format="json"
        )
        self.assertEqual(duplicate.status_code, 400)

    def test_draft_rejects_photo_from_another_product(self):
        image_id = self.upload(self.other)
        response = self.client.post(
            "/api/v1/listing-drafts/",
            {"product": str(self.product.pk), "channel": "mercado_livre", "image_ids": [image_id]},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(ListingDraft.objects.exists())

    def test_bad_upload_rejected_and_image_requires_login(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        bad = self.client.post(
            "/api/v1/product-images/",
            {"product": str(self.product.pk), "file": SimpleUploadedFile("bad.png", b"not an image")},
            format="multipart",
        )
        self.assertEqual(bad.status_code, 400)
        self.assertFalse(ProductImage.objects.exists())
        image_id = self.upload()
        content = self.client.get(f"/api/v1/product-images/{image_id}/content/")
        self.assertEqual(content.status_code, 200)
        self.assertEqual(content["Content-Type"], "image/png")
        self.assertTrue(b"".join(content.streaming_content).startswith(b"\x89PNG"))
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(f"/api/v1/product-images/{image_id}/content/").status_code, 401)

    def test_selected_photo_cannot_be_deleted_before_unlinking(self):
        image_id = self.upload()
        created = self.client.post(
            "/api/v1/listing-drafts/",
            {"product": str(self.product.pk), "channel": "shopee", "image_ids": [image_id]},
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(self.client.delete(f"/api/v1/product-images/{image_id}/").status_code, 400)
        updated = self.client.patch(
            f"/api/v1/listing-drafts/{created.json()['id']}/", {"image_ids": []}, format="json"
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(self.client.delete(f"/api/v1/product-images/{image_id}/").status_code, 204)
