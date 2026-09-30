from decimal import Decimal

from django.db import IntegrityError, transaction
from drf_spectacular.utils import extend_schema_field
from PIL import Image, UnidentifiedImageError
from rest_framework import serializers

from apps.common.domain.money import money
from apps.catalog.domain.gtin import gtin_error, normalize_gtin
from apps.catalog.domain.pricing import filament_cost
from apps.catalog.models import (
    Category,
    ListingDraft,
    ListingDraftImage,
    PrintingFilament,
    PrintingProfile,
    Product,
    ProductImage,
    default_category,
    printing_category,
)
from apps.supplies.domain.pricing import price_per_kg
from apps.supplies.models import Supply
from apps.inventory.models import Stock


MAX_FILAMENT_LINES = 8


class PrintingFilamentSerializer(serializers.ModelSerializer):
    filament = serializers.PrimaryKeyRelatedField(queryset=Supply.objects.select_related("category"))
    filament_name = serializers.CharField(source="filament.name", read_only=True)
    material = serializers.CharField(source="filament.material", read_only=True)
    color = serializers.CharField(source="filament.color", read_only=True)
    price_per_kg = serializers.SerializerMethodField()
    price_outdated = serializers.SerializerMethodField()
    # só na entrada: o dono pediu para trazer o preço atual do filamento para esta linha
    refresh_price = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = PrintingFilament
        fields = [
            "filament", "filament_name", "material", "color", "grams", "roll_price", "roll_weight_g",
            "price_per_kg", "price_outdated", "refresh_price",
        ]
        read_only_fields = ["roll_price", "roll_weight_g"]

    def get_price_per_kg(self, line) -> str:
        return f"{price_per_kg(line.roll_price, line.roll_weight_g):.2f}"

    def get_price_outdated(self, line) -> bool:
        supply = line.filament
        return line.roll_price != supply.roll_price or line.roll_weight_g != supply.roll_weight_g

    def validate_filament(self, supply):
        if not supply.category.is_filament or supply.roll_price is None or not supply.roll_weight_g:
            raise serializers.ValidationError("Escolha um insumo de filamento, com preço e peso do rolo.")
        return supply


class PrintingSerializer(serializers.ModelSerializer):
    filaments = PrintingFilamentSerializer(many=True, required=False)

    class Meta:
        model = PrintingProfile
        exclude = ["id", "product"]
        extra_kwargs = {"weight_g": {"required": False}}

    def validate_filaments(self, lines):
        if len(lines) > MAX_FILAMENT_LINES:
            raise serializers.ValidationError(f"Use no máximo {MAX_FILAMENT_LINES} filamentos por peça.")
        ids = [line["filament"].pk for line in lines]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("Não repita o mesmo filamento na peça.")
        product = getattr(self.parent, "instance", None)
        profile = PrintingProfile.objects.filter(product=product).first() if product else None
        already = set(profile.filaments.values_list("filament_id", flat=True)) if profile else set()
        for line in lines:
            supply = line["filament"]
            if not supply.active and supply.pk not in already:
                raise serializers.ValidationError(f"O filamento {supply.name} está inativo.")
        return lines


class CategorySerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Category
        fields = ["id", "name", "uses_printing_profile", "active", "products_count", "created_at", "updated_at"]
        read_only_fields = ["id", "products_count", "created_at", "updated_at"]

    def validate_name(self, value):
        name = " ".join(value.split())
        if not name:
            raise serializers.ValidationError("Informe o nome da categoria.")
        outras = Category.objects.all()
        if self.instance:
            outras = outras.exclude(pk=self.instance.pk)
        # casefold no Python: o iexact do SQLite não ignora maiúscula acentuada (Ô x ô)
        if any(nome.casefold() == name.casefold() for nome in outras.values_list("name", flat=True)):
            raise serializers.ValidationError("Já existe uma categoria com este nome.")
        return name

    def validate(self, attrs):
        flag = attrs.get("uses_printing_profile")
        if (
            self.instance
            and flag is not None
            and flag != self.instance.uses_printing_profile
            and self.instance.products.exists()
        ):
            raise serializers.ValidationError(
                {"uses_printing_profile": "A categoria já tem produtos: não dá para mudar o uso dos parâmetros 3D."}
            )
        return attrs


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False)
    category_name = serializers.CharField(source="category.name", read_only=True)
    gtin = serializers.CharField(max_length=30, required=False, allow_null=True, allow_blank=True)
    printing = PrintingSerializer(required=False, allow_null=True)
    quantity = serializers.IntegerField(source="stock.quantity", read_only=True, default=0)
    stock_value = serializers.DecimalField(
        source="stock.value", max_digits=14, decimal_places=2, read_only=True, default=0
    )
    average_cost = serializers.DecimalField(
        source="stock.average_cost", max_digits=18, decimal_places=6, read_only=True, default=0
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "sku",
            "gtin",
            "name",
            "category",
            "category_name",
            "brand",
            "model",
            "weight_g",
            "description",
            "cost_price",
            "sale_price",
            "active",
            "printing",
            "quantity",
            "stock_value",
            "average_cost",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "sku", "created_at", "updated_at"]

    def validate_gtin(self, value):
        code = normalize_gtin(value)
        if not code:
            return None
        erro = gtin_error(code)
        if erro:
            raise serializers.ValidationError(erro)
        outros = Product.objects.filter(gtin=code)
        if self.instance:
            outros = outros.exclude(pk=self.instance.pk)
        if outros.exists():
            raise serializers.ValidationError("Já existe um produto com este código de barras.")
        return code

    def validate(self, attrs):
        category = attrs.get("category")
        if category is None:
            if self.instance:
                category = self.instance.category
            else:
                # sem categoria: parâmetros 3D levam à de produção 3D, o resto à comum
                category = printing_category() if attrs.get("printing") else default_category()
                attrs["category"] = category
        elif not category.active and (not self.instance or self.instance.category_id != category.pk):
            raise serializers.ValidationError({"category": "Esta categoria está inativa."})
        profile = attrs.get("printing", getattr(self.instance, "printing", None))
        if category.uses_printing_profile and not profile:
            raise serializers.ValidationError({"printing": "Preencha os parâmetros de impressão 3D."})
        sent = attrs.get("printing")
        if category.uses_printing_profile and sent is not None and not sent.get("filaments"):
            existing = getattr(self.instance, "printing", None)
            if sent.get("weight_g") is None and not (existing and existing.weight_g):
                raise serializers.ValidationError(
                    {"printing": {"weight_g": "Informe o peso da peça ou escolha os filamentos."}}
                )
        if not category.uses_printing_profile and attrs.get("printing"):
            raise serializers.ValidationError({"printing": "Parâmetros 3D só valem em categoria de impressão 3D."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        profile = validated_data.pop("printing", None)
        product = Product.objects.create(**validated_data)
        Stock.objects.create(product=product)
        if profile:
            self._profile(product, profile)
        return product

    def _resolve_lines(self, lines, profile):
        """Linhas prontas para gravar, com o preço do rolo copiado. Linha que já existia mantém o
        preço que tinha, a menos que o dono peça o preço atual (`refresh_price`)."""
        kept = {line.filament_id: line for line in profile.filaments.all()} if profile else {}
        resolved = []
        for position, line in enumerate(lines):
            supply, old = line["filament"], kept.get(line["filament"].pk)
            fresh = old is None or line.get("refresh_price")
            resolved.append(
                {
                    "filament": supply,
                    "grams": line["grams"],
                    "roll_price": supply.roll_price if fresh else old.roll_price,
                    "roll_weight_g": supply.roll_weight_g if fresh else old.roll_weight_g,
                    "position": position,
                }
            )
        return resolved

    def _profile(self, product, data):
        lines = data.pop("filaments", None)
        profile = PrintingProfile.objects.filter(product=product).first()
        resolved = self._resolve_lines(lines, profile) if lines else []
        if resolved:
            grams = sum((line["grams"] for line in resolved), Decimal(0))
            cost = filament_cost((line["grams"], line["roll_price"], line["roll_weight_g"]) for line in resolved)
            # com linhas, o peso da peça é a soma delas; o preço por kg guardado é a média ponderada
            data["weight_g"] = grams
            data["filament_price_kg"] = money(cost / grams * 1000)
        profile, _ = PrintingProfile.objects.update_or_create(product=product, defaults=data)
        if lines is not None:
            profile.filaments.exclude(filament_id__in=[line["filament"].pk for line in resolved]).delete()
            for line in resolved:
                PrintingFilament.objects.update_or_create(
                    profile=profile,
                    filament=line["filament"],
                    defaults={k: line[k] for k in ("grams", "roll_price", "roll_weight_g", "position")},
                )
        product.cost_price, product.sale_price = profile.prices()
        product.save(update_fields=["cost_price", "sale_price", "updated_at"])

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = Product.objects.select_for_update().get(pk=instance.pk)
        profile = validated_data.pop("printing", None)
        instance = super().update(instance, validated_data)
        if instance.category.uses_printing_profile:
            self._profile(instance, profile or {})
        else:
            PrintingProfile.objects.filter(product=instance).delete()
        return instance


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


class ListingDraftSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=0, required=False, allow_null=True
    )
    image_ids = serializers.PrimaryKeyRelatedField(
        queryset=ProductImage.objects.all(), many=True, required=False, source="images"
    )
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    # preenchido quando o rascunho já virou anúncio (spec 012)
    published_item_id = serializers.CharField(source="listing.item_id", read_only=True, allow_null=True)
    pending_changes = serializers.SerializerMethodField()

    @extend_schema_field(serializers.BooleanField())
    def get_pending_changes(self, draft):
        """Rascunho publicado e salvo depois do último envio ao anúncio."""
        # o acesso reverso sem vínculo levanta um AttributeError: getattr devolve None
        listing = getattr(draft, "listing", None)
        if not listing:
            return False
        return listing.pushed_at is None or draft.updated_at > listing.pushed_at

    class Meta:
        model = ListingDraft
        fields = [
            "id", "product", "product_name", "product_sku", "channel", "title", "description",
            "price", "brand", "model", "condition", "category_id", "attributes", "image_ids",
            "published_item_id", "pending_changes", "created_at", "updated_at",
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
