from rest_framework import serializers

from apps.accounts.serializers import PublicUserSerializer

from .models import LandlordReview, PropertyReview


class PropertyReviewSerializer(serializers.ModelSerializer):
    user = PublicUserSerializer(read_only=True)

    class Meta:
        model = PropertyReview
        fields = ["id", "user", "rating", "title", "comment", "created_at"]


class PropertyReviewWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyReview
        fields = ["rating", "title", "comment"]


class LandlordReviewSerializer(serializers.ModelSerializer):
    reviewer = PublicUserSerializer(read_only=True)
    like_count = serializers.ReadOnlyField()
    is_liked_by_me = serializers.SerializerMethodField()

    class Meta:
        model = LandlordReview
        fields = ["id", "reviewer", "rating", "comment", "like_count", "is_liked_by_me", "created_at"]

    def get_is_liked_by_me(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(pk=request.user.pk).exists()


class LandlordReviewWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandlordReview
        fields = ["rating", "comment"]
