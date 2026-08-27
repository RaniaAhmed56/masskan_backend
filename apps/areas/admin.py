from django.contrib import admin

from .models import Area, AreaReview, NearbyPlace


class NearbyPlaceInline(admin.TabularInline):
    model = NearbyPlace
    extra = 1


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "safety", "quietness", "transport", "price_level"]
    search_fields = ["name", "city"]
    inlines = [NearbyPlaceInline]


@admin.register(AreaReview)
class AreaReviewAdmin(admin.ModelAdmin):
    list_display = ["area", "user", "rating", "created_at"]
    list_filter = ["rating"]
    autocomplete_fields = ["user"]
    search_fields = ["area__name", "user__email"]
