from rest_framework import serializers

from apps.accounts.serializers import PublicUserSerializer

from .models import Area, AreaReview, NearbyPlace


class NearbyPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NearbyPlace
        fields = ["id", "name", "category", "distance_label"]


class AreaReviewSerializer(serializers.ModelSerializer):
    user = PublicUserSerializer(read_only=True)
    helpful_count = serializers.ReadOnlyField()
    is_helpful_by_me = serializers.SerializerMethodField()

    class Meta:
        model = AreaReview
        fields = ["id", "user", "rating", "comment", "helpful_count", "is_helpful_by_me", "created_at"]

    def get_is_helpful_by_me(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.helpful_votes.filter(user=request.user).exists()


class AreaReviewWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaReview
        fields = ["rating", "comment"]


class AreaSerializer(serializers.ModelSerializer):
    """Full "Neighborhood Insights" payload for one area — one call gives
    apartment-details.tsx everything area-rating.tsx renders."""

    nearby_places = NearbyPlaceSerializer(many=True, read_only=True)
    average_rating = serializers.ReadOnlyField()
    review_count = serializers.ReadOnlyField()
    rating_breakdown = serializers.SerializerMethodField()

    class Meta:
        model = Area
        fields = [
            "id",
            "name",
            "city",
            "safety",
            "quietness",
            "amenities_score",
            "transport",
            "schools",
            "entertainment",
            "family_friendly_score",
            "student_friendly_score",
            "price_level",
            "avg_price_min",
            "avg_price_max",
            "demand_trend",
            "nearby_places",
            "average_rating",
            "review_count",
            "rating_breakdown",
        ]

    def get_rating_breakdown(self, obj):
        """{5: pct, 4: pct, ...} — the horizontal bar-per-star-rating widget."""
        counts = {star: 0 for star in range(1, 6)}
        total = 0
        for rating in obj.reviews.values_list("rating", flat=True):
            counts[rating] = counts.get(rating, 0) + 1
            total += 1
        if not total:
            return {str(star): 0 for star in range(5, 0, -1)}
        return {str(star): round(counts[star] * 100 / total) for star in range(5, 0, -1)}
