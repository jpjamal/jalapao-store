from django.contrib import admin

from .models import Listing, MarketplaceAccount, OutboxEvent


@admin.register(MarketplaceAccount)
class MarketplaceAccountAdmin(admin.ModelAdmin):
    list_display = ["channel", "external_id", "name", "active", "authorization_expires_at"]
    list_filter = ["channel", "active"]
    # token não aparece no admin: quem precisa dele é o código, não a tela
    exclude = ["access_token", "refresh_token"]


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ["marketplace", "item_id", "product", "sync_enabled", "remote_stock"]
    list_filter = ["marketplace", "sync_enabled"]
    search_fields = ["item_id", "title", "product__name", "product__sku"]


@admin.register(OutboxEvent)
class OutboxEventAdmin(admin.ModelAdmin):
    list_display = ["topic", "created_at", "delivered_at", "attempts"]
    list_filter = ["topic"]
