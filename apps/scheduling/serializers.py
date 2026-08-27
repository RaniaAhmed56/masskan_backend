from rest_framework import serializers

from apps.accounts.serializers import PublicUserSerializer
from apps.properties.serializers import PropertyListSerializer

from .models import VisitRequest


class VisitRequestSerializer(serializers.ModelSerializer):
    """Read shape — buyer-dashboard.tsx "Visits" tab / seller-dashboard.tsx
    incoming-requests list."""

    property = PropertyListSerializer(read_only=True)
    requester = PublicUserSerializer(read_only=True)
    landlord = PublicUserSerializer(read_only=True)

    class Meta:
        model = VisitRequest
        fields = [
            "id",
            "property",
            "requester",
            "landlord",
            "full_name",
            "email",
            "phone",
            "visit_date",
            "visit_time",
            "notes",
            "status",
            "landlord_note",
            "created_at",
        ]


class VisitRequestCreateSerializer(serializers.ModelSerializer):
    """POST body — the booking form on schedule.tsx."""

    property_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = VisitRequest
        fields = ["property_id", "full_name", "email", "phone", "visit_date", "visit_time", "notes"]


class VisitRequestStatusSerializer(serializers.Serializer):
    """POST .../confirm|cancel|complete/ optional body — an optional note
    from the landlord (e.g. a reschedule reason)."""

    landlord_note = serializers.CharField(required=False, allow_blank=True, max_length=255)
