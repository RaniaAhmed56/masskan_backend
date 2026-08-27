from rest_framework import serializers

from apps.accounts.serializers import PublicUserSerializer

from .models import AISearchLog, Amenity, Favorite, Property, PropertyImage


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ["key", "label"]


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ["id", "image", "order", "is_primary"]


class PropertyListSerializer(serializers.ModelSerializer):
    """Compact shape for grid/card views (search-results.tsx, landing-page.tsx
    Featured Properties, buyer/seller dashboards)."""

    primary_image = serializers.SerializerMethodField()
    area_m2 = serializers.ReadOnlyField()
    average_rating = serializers.ReadOnlyField()
    review_count = serializers.ReadOnlyField()
    amenities = AmenitySerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    owner_id = serializers.IntegerField(read_only=True)
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "property_type",
            "price",
            "city",
            "area_name",
            "address",
            "bedrooms",
            "bathrooms",
            "area_sqft",
            "area_m2",
            "furnished",
            "pet_friendly",
            "amenities",
            "primary_image",
            "average_rating",
            "review_count",
            "is_favorited",
            "is_featured",
            "status",
            "owner_id",
            "owner_name",
            "created_at",
            "latitude",
            "longitude",
        ]

    def get_primary_image(self, obj):
        image = next((img for img in obj.images.all() if img.is_primary), None) or next(
            iter(obj.images.all()), None
        )
        if not image:
            return None
        request = self.context.get("request")
        url = image.image.url
        return request.build_absolute_uri(url) if request else url

    def get_is_favorited(self, obj):
        # One extra query per row (bounded by page_size, currently 12) —
        # simplest correct implementation. If this ever shows up in
        # profiling, annotate it in the view with a Prefetch instead.
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.favorited_by.filter(user=request.user).exists()


class PropertyDetailSerializer(PropertyListSerializer):
    images = PropertyImageSerializer(many=True, read_only=True)
    owner = PublicUserSerializer(read_only=True)

    class Meta(PropertyListSerializer.Meta):
        fields = PropertyListSerializer.Meta.fields + [
            "description",
            "images",
            "floor",
            "available_from",
            "lease_term_months",
            "near_public_transport",
            "view_count",
            "owner",
            "updated_at",
        ]


class PropertyWriteSerializer(serializers.ModelSerializer):
    """Create/update — add-listing.tsx. `amenities` accepts a list of
    Amenity `key`s (not IDs) so the frontend never has to know the DB's
    primary keys, only the same string keys it already renders icons from.
    """

    amenities = serializers.SlugRelatedField(
        slug_field="key", queryset=Amenity.objects.all(), many=True, required=False
    )

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "description",
            "property_type",
            "price",
            "bedrooms",
            "bathrooms",
            "area_sqft",
            "floor",
            "address",
            "city",
            "area_name",
            "latitude",
            "longitude",
            "near_public_transport",
            "furnished",
            "pet_friendly",
            "amenities",
            "available_from",
            "lease_term_months",
            "status",
        ]
        read_only_fields = ["id", "status"]

    def create(self, validated_data):
        amenities = validated_data.pop("amenities", [])
        validated_data["owner"] = self.context["request"].user
        # Every new listing starts pending — mirrors admin-dashboard.tsx's
        # moderation queue, which is the only path to `active`.
        validated_data["status"] = Property.Status.PENDING
        property_obj = Property.objects.create(**validated_data)
        property_obj.amenities.set(amenities)
        return property_obj

    def update(self, instance, validated_data):
        amenities = validated_data.pop("amenities", None)
        # Editing a listing sends it back for re-approval rather than
        # silently letting an owner change price/description on a live,
        # already-vetted listing.
        if instance.status == Property.Status.ACTIVE:
            validated_data["status"] = Property.Status.PENDING
        instance = super().update(instance, validated_data)
        if amenities is not None:
            instance.amenities.set(amenities)
        return instance


class PropertyModerationSerializer(serializers.Serializer):
    """POST /properties/{id}/reject/ body — approve/ takes no body."""

    reason = serializers.CharField(required=False, allow_blank=True)


class FavoriteSerializer(serializers.ModelSerializer):
    property = PropertyListSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ["id", "property", "created_at"]


class AISearchRequestSerializer(serializers.Serializer):
    """Shape matches the 5 steps of ai-search-questionnaire.tsx exactly:
    budget, property type, location/commute, amenities, pets."""

    min_budget = serializers.IntegerField(required=False, min_value=0)
    max_budget = serializers.IntegerField(required=False, min_value=0)
    bedrooms = serializers.CharField(required=False, allow_blank=True)
    property_type = serializers.CharField(required=False, allow_blank=True)
    area_type = serializers.CharField(required=False, allow_blank=True, help_text="e.g. 'city-center', 'suburb'.")
    work_area = serializers.CharField(required=False, allow_blank=True)
    study_area = serializers.CharField(required=False, allow_blank=True)
    needs_public_transport = serializers.BooleanField(required=False, default=False)
    amenities = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    pet_friendly = serializers.BooleanField(required=False, default=False)


class AISearchResultSerializer(PropertyListSerializer):
    match_score = serializers.IntegerField(read_only=True)
    match_reason = serializers.CharField(read_only=True)

    class Meta(PropertyListSerializer.Meta):
        fields = PropertyListSerializer.Meta.fields + ["match_score", "match_reason"]


class AISearchLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AISearchLog
        fields = ["id", "criteria", "result_count", "created_at"]
