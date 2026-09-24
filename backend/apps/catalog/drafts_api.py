from django.db import IntegrityError, transaction
from django.http import FileResponse, Http404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from PIL import Image, UnidentifiedImageError
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .models import ListingDraft, ListingDraftImage, Product, ProductImage


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "product", "alt_text", "position", "mime_type", "width", "height", "size_bytes", "created_at"]
        read_only_fields = fields


class ProductImageUploadSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    file = serializers.FileField()
    alt_text = serializers.CharField(max_length=200, required=False, allow_blank=True)
    position = serializers.IntegerField(min_value=0, max_value=65535, required=False, default=0)

    def validate_file(self, uploaded):
        if uploaded.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("A imagem deve ter no máximo 10 MB.")
        try:
            with Image.open(uploaded) as image:
                image_format = image.format
                width, height = image.size
                if image_format not in {"JPEG", "PNG", "WEBP"}:
                    raise serializers.ValidationError("Envie uma imagem JPG, PNG ou WebP.")
                if not (1 <= width <= 6000 and 1 <= height <= 6000) or width * height > 25_000_000:
                    raise serializers.ValidationError("A imagem excede o limite de dimensões.")
                image.verify()
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
            raise serializers.ValidationError("Arquivo de imagem inválido.") from exc
        finally:
            uploaded.seek(0)
        extension = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}[image_format]
        uploaded.name = f"upload.{extension}"
        uploaded.detected_mime_type = Image.MIME[image_format]
        uploaded.detected_size = (width, height)
        return uploaded

    def create(self, validated_data):
        uploaded = validated_data["file"]
        width, height = uploaded.detected_size
        return ProductImage.objects.create(
            product=validated_data["product"],
            file=uploaded,
            alt_text=validated_data.get("alt_text", ""),
            position=validated_data["position"],
            mime_type=uploaded.detected_mime_type,
            width=width,
            height=height,
            size_bytes=uploaded.size,
        )


class ProductImageViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    queryset = ProductImage.objects.select_related("product").all()
    filterset_fields = ["product"]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        return ProductImageUploadSerializer if self.action == "create" else ProductImageSerializer

    @extend_schema(request=ProductImageUploadSerializer, responses={201: ProductImageSerializer})
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        image = serializer.save()
        return Response(ProductImageSerializer(image).data, status=201)

    def destroy(self, request, *args, **kwargs):
        image = self.get_object()
        if image.drafts.exists():
            raise serializers.ValidationError({"image": "Retire a foto dos rascunhos antes de excluí-la."})
        file = image.file
        image.delete()
        file.delete(save=False)
        return Response(status=204)

    @extend_schema(responses={200: OpenApiTypes.BINARY})
    @action(detail=True, methods=["get"], url_path="content")
    def content(self, request, pk=None):
        image = self.get_object()
        try:
            return FileResponse(image.file.open("rb"), content_type=image.mime_type)
        except FileNotFoundError as exc:
            raise Http404("Foto não encontrada no armazenamento.") from exc


class ListingDraftSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=0, required=False, allow_null=True
    )
    image_ids = serializers.PrimaryKeyRelatedField(
        queryset=ProductImage.objects.all(), many=True, required=False, source="images"
    )
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)

    class Meta:
        model = ListingDraft
        fields = [
            "id", "product", "product_name", "product_sku", "channel", "title", "description",
            "price", "brand", "model", "condition", "category_id", "attributes", "image_ids",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "product_name", "product_sku", "created_at", "updated_at"]

    def validate(self, attrs):
        product = attrs.get("product", getattr(self.instance, "product", None))
        channel = attrs.get("channel", getattr(self.instance, "channel", None))
        if not self.instance and ListingDraft.objects.filter(product=product, channel=channel).exists():
            raise serializers.ValidationError({"channel": "Já existe um rascunho deste produto neste canal."})
        if self.instance and ("product" in attrs and product != self.instance.product or
                              "channel" in attrs and attrs["channel"] != self.instance.channel):
            raise serializers.ValidationError("Produto e canal não podem ser alterados neste rascunho.")
        images = attrs.get("images")
        if images is not None:
            if len(images) > 30:
                raise serializers.ValidationError({"image_ids": "Escolha no máximo 30 fotos por rascunho."})
            if len(images) != len({image.pk for image in images}):
                raise serializers.ValidationError({"image_ids": "Não repita a mesma foto."})
            if any(image.product_id != product.pk for image in images):
                raise serializers.ValidationError({"image_ids": "Use apenas fotos deste produto."})
        if "attributes" in attrs and not isinstance(attrs["attributes"], dict):
            raise serializers.ValidationError({"attributes": "Informe um objeto de atributos."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        images = validated_data.pop("images", [])
        try:
            draft = ListingDraft.objects.create(**validated_data)
        except IntegrityError as exc:
            raise serializers.ValidationError({"channel": "Já existe um rascunho deste produto neste canal."}) from exc
        self._replace_images(draft, images)
        return draft

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = ListingDraft.objects.select_for_update().get(pk=instance.pk)
        images = validated_data.pop("images", None)
        instance = super().update(instance, validated_data)
        if images is not None:
            self._replace_images(instance, images)
        return instance

    @staticmethod
    def _replace_images(draft, images):
        draft.ordered_images.all().delete()
        ListingDraftImage.objects.bulk_create([
            ListingDraftImage(draft=draft, image=image, position=position)
            for position, image in enumerate(images)
        ])

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["image_ids"] = list(instance.ordered_images.values_list("image_id", flat=True))
        return data


class ListingDraftViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
    mixins.UpdateModelMixin, viewsets.GenericViewSet,
):
    queryset = ListingDraft.objects.select_related("product").prefetch_related("ordered_images").all()
    serializer_class = ListingDraftSerializer
    filterset_fields = ["product", "channel"]
