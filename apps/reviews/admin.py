from django.contrib import admin

from .models import LandlordReview, PropertyReview


@admin.register(PropertyReview)
class PropertyReviewAdmin(admin.ModelAdmin):
    list_display = ["property", "user", "rating", "created_at"]
    list_filter = ["rating"]
    autocomplete_fields = ["property", "user"]
    search_fields = ["property__title", "user__email"]


@admin.register(LandlordReview)
class LandlordReviewAdmin(admin.ModelAdmin):
    list_display = ["landlord", "reviewer", "rating", "created_at"]
    list_filter = ["rating"]
    autocomplete_fields = ["landlord", "reviewer"]
    search_fields = ["landlord__email", "reviewer__email"]
