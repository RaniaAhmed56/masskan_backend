from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.models import User
from apps.notifications.models import Notification
from apps.notifications.services import notify
from apps.properties.models import Property

from .models import LandlordReview, PropertyReview
from .serializers import (
    LandlordReviewSerializer,
    LandlordReviewWriteSerializer,
    PropertyReviewSerializer,
    PropertyReviewWriteSerializer,
)


class PropertyReviewViewSet(viewsets.ModelViewSet):
    """/api/v1/reviews/properties/{property_id}/reviews/

    Nested under a property id (rather than a flat /reviews/{id}/) because
    every read the frontend does is "reviews for this listing" — apartment-
    details.tsx never needs a single review in isolation.
    """

    serializer_class = PropertyReviewSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return PropertyReview.objects.filter(property_id=self.kwargs["property_id"]).select_related("user")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PropertyReviewWriteSerializer
        return PropertyReviewSerializer

    def create(self, request, *args, **kwargs):
        property_obj = get_object_or_404(Property, pk=self.kwargs["property_id"])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review, _created = PropertyReview.objects.update_or_create(
            property=property_obj, user=request.user, defaults=serializer.validated_data
        )
        return Response(PropertyReviewSerializer(review, context={"request": request}).data, status=201)


class LandlordReviewViewSet(viewsets.ModelViewSet):
    """/api/v1/reviews/landlords/{landlord_id}/reviews/ — landlord-profile.tsx."""

    serializer_class = LandlordReviewSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return LandlordReview.objects.filter(landlord_id=self.kwargs["landlord_id"]).select_related("reviewer")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return LandlordReviewWriteSerializer
        return LandlordReviewSerializer

    def create(self, request, *args, **kwargs):
        landlord = get_object_or_404(User, pk=self.kwargs["landlord_id"])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review, created = LandlordReview.objects.update_or_create(
            landlord=landlord, reviewer=request.user, defaults=serializer.validated_data
        )
        if created:
            notify(
                user=landlord,
                type=Notification.NotificationType.NEW_REVIEW,
                message=f"{request.user.full_name} left you a {review.rating}-star review.",
                link="/landlord-profile",
            )
        return Response(LandlordReviewSerializer(review, context={"request": request}).data, status=201)

    @action(detail=True, methods=["post"])
    def like(self, request, landlord_id=None, pk=None):
        """POST .../reviews/{id}/like/ — toggle, backs the 👍 button."""
        review = get_object_or_404(LandlordReview, pk=pk, landlord_id=landlord_id)
        if review.likes.filter(pk=request.user.pk).exists():
            review.likes.remove(request.user)
            liked = False
        else:
            review.likes.add(request.user)
            liked = True
        return Response({"is_liked_by_me": liked, "like_count": review.like_count})
