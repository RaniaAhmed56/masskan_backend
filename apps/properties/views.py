from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsAdminRole, IsLandlord, IsOwnerOrReadOnly
from apps.notifications.models import Notification
from apps.notifications.services import notify

from .filters import PropertyFilter
from .models import AISearchLog, Amenity, Favorite, Property, PropertyImage
from .serializers import (
    AISearchLogSerializer,
    AISearchRequestSerializer,
    AISearchResultSerializer,
    AmenitySerializer,
    FavoriteSerializer,
    PropertyDetailSerializer,
    PropertyImageSerializer,
    PropertyListSerializer,
    PropertyModerationSerializer,
    PropertyWriteSerializer,
)
from .services import score_properties


class AmenityViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/v1/properties/amenities/ — the seeded lookup list, used to
    populate every amenity checkbox/filter in the frontend."""

    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class PropertyViewSet(viewsets.ModelViewSet):
    """/api/v1/properties/properties/

    Public browsing (search-results.tsx, landing-page.tsx) + owner-managed
    CRUD (add-listing.tsx, seller-dashboard.tsx) + admin moderation
    (admin-dashboard.tsx) all live on this one resource, split out via the
    extra actions below rather than three separate viewsets, since they all
    operate on the same `Property` object.
    """

    # Restrict pk matching to digits so this viewset's router-generated
    # `{pk}/` pattern can't accidentally swallow sibling routes registered
    # on the same router (e.g. `amenities/`) — see urls.py.
    lookup_value_regex = "[0-9]+"

    filterset_class = PropertyFilter
    search_fields = ["title", "description", "city", "area_name"]
    ordering_fields = ["price", "created_at", "view_count", "bedrooms"]
    ordering = ["-is_featured", "-created_at"]

    def get_permissions(self):
        if self.action in ("create",):
            return [permissions.IsAuthenticated(), IsLandlord()]
        if self.action in ("update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        if self.action in ("pending", "approve", "reject"):
            return [IsAdminRole()]
        if self.action in ("mine", "favorite", "favorites", "images"):
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return PropertyWriteSerializer
        if self.action == "retrieve":
            return PropertyDetailSerializer
        return PropertyListSerializer

    def get_queryset(self):
        qs = Property.objects.select_related("owner").prefetch_related("images", "amenities")
        user = self.request.user
        if self.action in ("list", "retrieve"):
            if user.is_authenticated and user.is_staff:
                return qs
            if user.is_authenticated:
                return qs.filter(models.Q(status=Property.Status.ACTIVE) | models.Q(owner=user))
            return qs.filter(status=Property.Status.ACTIVE)
        return qs

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        Property.objects.filter(pk=instance.pk).update(view_count=models.F("view_count") + 1)
        instance.refresh_from_db(fields=["view_count"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    # ------------------------------------------------------------------
    # Read-only convenience endpoints
    # ------------------------------------------------------------------
    @action(detail=False)
    def featured(self, request):
        """GET /properties/featured/ — landing-page.tsx Featured Properties grid."""
        qs = self.get_queryset().filter(status=Property.Status.ACTIVE, is_featured=True)[:8]
        serializer = PropertyListSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    @action(detail=False)
    def mine(self, request):
        """GET /properties/mine/ — every listing the logged-in landlord
        owns, any status (seller-dashboard.tsx All/Active/Pending tabs)."""
        qs = self.get_queryset().filter(owner=request.user)
        status_param = request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        page = self.paginate_queryset(qs)
        serializer = PropertyListSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    # ------------------------------------------------------------------
    # Favorites
    # ------------------------------------------------------------------
    @action(detail=True, methods=["post"])
    def favorite(self, request, pk=None):
        """POST /properties/{id}/favorite/ — toggles the heart icon."""
        property_obj = get_object_or_404(Property, pk=pk)
        favorite, created = Favorite.objects.get_or_create(user=request.user, property=property_obj)
        if not created:
            favorite.delete()
            return Response({"is_favorited": False})
        return Response({"is_favorited": True}, status=status.HTTP_201_CREATED)

    @action(detail=False)
    def favorites(self, request):
        """GET /properties/favorites/ — profile.tsx / buyer-dashboard.tsx Saved tab."""
        qs = Favorite.objects.filter(user=request.user).select_related("property").order_by("-created_at")
        page = self.paginate_queryset(qs)
        serializer = FavoriteSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    # ------------------------------------------------------------------
    # Images
    # ------------------------------------------------------------------
    @action(detail=True, methods=["post"], url_path="images")
    def upload_image(self, request, pk=None):
        """POST /properties/{id}/images/ (multipart, field name `image`)
        — add-listing.tsx's photo upload step."""
        property_obj = get_object_or_404(Property, pk=pk)
        if property_obj.owner_id != request.user.id and not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        from django.conf import settings as django_settings

        if property_obj.images.count() >= django_settings.MAX_PROPERTY_IMAGES:
            return Response(
                {"detail": f"Maximum {django_settings.MAX_PROPERTY_IMAGES} images per listing."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        image = PropertyImage.objects.create(
            property=property_obj,
            image=request.FILES["image"],
            order=property_obj.images.count(),
            is_primary=not property_obj.images.exists(),
        )
        return Response(PropertyImageSerializer(image).data, status=status.HTTP_201_CREATED)

    # ------------------------------------------------------------------
    # Admin moderation
    # ------------------------------------------------------------------
    @action(detail=False)
    def pending(self, request):
        """GET /properties/pending/ — admin-dashboard.tsx moderation queue."""
        qs = Property.objects.filter(status=Property.Status.PENDING).select_related("owner")
        page = self.paginate_queryset(qs)
        serializer = PropertyListSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        property_obj = get_object_or_404(Property, pk=pk)
        property_obj.status = Property.Status.ACTIVE
        property_obj.rejection_reason = ""
        property_obj.save(update_fields=["status", "rejection_reason"])
        notify(
            user=property_obj.owner,
            type=Notification.NotificationType.LISTING_APPROVED,
            message=f"Your listing '{property_obj.title}' was approved and is now live.",
            link="/seller-dashboard",
        )
        return Response(PropertyDetailSerializer(property_obj, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        serializer = PropertyModerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        property_obj = get_object_or_404(Property, pk=pk)
        property_obj.status = Property.Status.REJECTED
        property_obj.rejection_reason = serializer.validated_data.get("reason", "")
        property_obj.save(update_fields=["status", "rejection_reason"])
        notify(
            user=property_obj.owner,
            type=Notification.NotificationType.LISTING_REJECTED,
            message=f"Your listing '{property_obj.title}' was rejected.",
            link="/seller-dashboard",
        )
        return Response(PropertyDetailSerializer(property_obj, context={"request": request}).data)


class AISearchView(APIView):
    """POST /api/v1/properties/ai-search/

    Body: AISearchRequestSerializer (the 5-step questionnaire answers).
    Returns the top-scoring active properties with `match_score` (0-100)
    and a human-readable `match_reason` — backs ai-search-results.tsx.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        request_serializer = AISearchRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        criteria = request_serializer.validated_data

        from django.conf import settings as django_settings

        queryset = Property.objects.filter(status=Property.Status.ACTIVE).prefetch_related("images", "amenities")
        scored = score_properties(queryset, criteria, limit=django_settings.AI_MATCH_RESULTS_LIMIT)

        results = []
        for item in scored:
            data = AISearchResultSerializer(item.property, context={"request": request}).data
            data["match_score"] = item.score
            data["match_reason"] = item.reason
            results.append(data)

        AISearchLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            criteria=criteria,
            result_count=len(results),
        )

        return Response({"count": len(results), "results": results})


class AISearchHistoryView(APIView):
    """GET /api/v1/properties/ai-search/history/ — a signed-in user's past
    questionnaire submissions (used to prefill the form / show "last search")."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        logs = AISearchLog.objects.filter(user=request.user)[:10]
        return Response(AISearchLogSerializer(logs, many=True).data)
