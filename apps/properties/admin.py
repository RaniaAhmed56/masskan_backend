from django.contrib import admin

from .models import AISearchLog, Amenity, Favorite, Property, PropertyImage


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "property_type", "price", "city", "status", "is_featured", "created_at"]
    list_filter = ["status", "property_type", "furnished", "pet_friendly", "is_featured", "city"]
    search_fields = ["title", "description", "city", "owner__email"]
    autocomplete_fields = ["owner"]
    filter_horizontal = ["amenities"]
    inlines = [PropertyImageInline]
    actions = ["approve_listings", "reject_listings"]

    @admin.action(description="Approve selected listings")
    def approve_listings(self, request, queryset):
        queryset.update(status=Property.Status.ACTIVE, rejection_reason="")

    @admin.action(description="Reject selected listings")
    def reject_listings(self, request, queryset):
        queryset.update(status=Property.Status.REJECTED)


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ["label", "key"]
    search_fields = ["label", "key"]


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ["user", "property", "created_at"]
    autocomplete_fields = ["user", "property"]
    search_fields = ["user__email", "property__title"]


@admin.register(AISearchLog)
class AISearchLogAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "result_count", "created_at"]
    readonly_fields = ["criteria"]
