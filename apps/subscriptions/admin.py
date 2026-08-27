from django.contrib import admin

from .models import PlanFeature, Subscription, SubscriptionPlan


class PlanFeatureInline(admin.TabularInline):
    model = PlanFeature
    extra = 1


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ["name", "role", "price_monthly", "is_popular", "sort_order"]
    list_filter = ["role", "is_popular"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ["name"]}
    inlines = [PlanFeatureInline]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "plan", "status", "started_at", "current_period_end"]
    list_filter = ["status", "plan"]
    autocomplete_fields = ["user", "plan"]
    search_fields = ["user__email"]
