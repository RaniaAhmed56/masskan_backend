from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Area, AreaReview, AreaReviewHelpfulVote
from .serializers import AreaReviewSerializer, AreaReviewWriteSerializer, AreaSerializer


class AreaViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/v1/areas/ and /api/v1/areas/{name}/ (lookup by area name,
    not numeric id, since that's what apartment-details.tsx has on hand —
    `Property.area_name`)."""

    queryset = Area.objects.prefetch_related("nearby_places", "reviews")
    serializer_class = AreaSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "name"
    lookup_value_regex = "[^/]+"
    pagination_class = None

    @action(detail=True, methods=["get", "post"])
    def reviews(self, request, name=None):
        """GET returns every review for the area unpaginated (review
        volume per neighborhood is small); POST creates-or-updates the
        current user's own review (one review per user per area)."""
        area = self.get_object()
        if request.method == "GET":
            qs = area.reviews.select_related("user")
            serializer = AreaReviewSerializer(qs, many=True, context={"request": request})
            return Response(serializer.data)

        if not request.user.is_authenticated:
            return Response(status=401)
        serializer = AreaReviewWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review, _created = AreaReview.objects.update_or_create(
            area=area, user=request.user, defaults=serializer.validated_data
        )
        return Response(AreaReviewSerializer(review, context={"request": request}).data, status=201)


class AreaReviewHelpfulView(generics.GenericAPIView):
    """POST /api/v1/areas/reviews/{review_id}/helpful/ — toggle, matching
    the frontend's optimistic toggleHelpful(idx) button."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, review_id):
        review = get_object_or_404(AreaReview, pk=review_id)
        vote, created = AreaReviewHelpfulVote.objects.get_or_create(review=review, user=request.user)
        if not created:
            vote.delete()
            return Response({"is_helpful_by_me": False, "helpful_count": review.helpful_count})
        return Response({"is_helpful_by_me": True, "helpful_count": review.helpful_count})
