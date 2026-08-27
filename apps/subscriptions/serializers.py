from rest_framework import serializers

from .models import PlanFeature, Subscription, SubscriptionPlan


class PlanFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanFeature
        fields = ["text", "included"]


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    features = PlanFeatureSerializer(many=True, read_only=True)

    class Meta:
        model = SubscriptionPlan
        fields = [
            "id",
            "role",
            "name",
            "slug",
            "price_monthly",
            "description",
            "icon",
            "is_popular",
            "max_active_listings",
            "max_saved_properties",
            "max_landlord_contacts_per_month",
            "has_ai_matching",
            "has_priority_support",
            "features",
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = ["id", "plan", "status", "started_at", "current_period_end", "cancelled_at", "created_at"]


class SubscribeRequestSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
