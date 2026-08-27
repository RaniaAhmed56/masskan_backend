from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.permissions import IsSearcher
from apps.common.services.notifications import send_transactional_email
from apps.notifications.models import Notification
from apps.notifications.services import notify
from apps.properties.models import Property

from .models import VisitRequest
from .serializers import VisitRequestCreateSerializer, VisitRequestSerializer, VisitRequestStatusSerializer


class VisitRequestViewSet(viewsets.ModelViewSet):
    """/api/v1/scheduling/visits/ — schedule.tsx's booking form plus the
    "Visits" tabs on buyer-dashboard.tsx (as requester) and
    seller-dashboard.tsx (as landlord).

    There's no generic `list`/`update`/`destroy` here — only the
    `mine`/`received` read actions and the status-transition actions below,
    since a visit request's lifecycle is a fixed workflow, not free-form
    editing.
    """

    http_method_names = ["get", "post", "head", "options"]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return VisitRequest.objects.select_related("property", "property__owner", "requester")

    def get_serializer_class(self):
        if self.action == "create":
            return VisitRequestCreateSerializer
        return VisitRequestSerializer

    def get_permissions(self):
        if self.action == "create":
            return [permissions.IsAuthenticated(), IsSearcher()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        property_obj = get_object_or_404(Property, pk=data.pop("property_id"))

        visit = VisitRequest.objects.create(property=property_obj, requester=request.user, **data)

        send_transactional_email(
            to=property_obj.owner.email,
            subject="New visit request — Masskan",
            message=(
                f"{visit.full_name} requested a visit to '{property_obj.title}' "
                f"on {visit.visit_date} at {visit.visit_time}."
            ),
        )
        notify(
            user=property_obj.owner,
            type=Notification.NotificationType.VISIT_REQUESTED,
            message=f"{visit.full_name} requested a visit to '{property_obj.title}'.",
            link="/schedule",
        )
        return Response(VisitRequestSerializer(visit, context={"request": request}).data, status=201)

    @action(detail=False)
    def mine(self, request):
        """GET /visits/mine/ — visits *I* booked (buyer-dashboard.tsx)."""
        qs = self.get_queryset().filter(requester=request.user)
        status_param = request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        serializer = VisitRequestSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    @action(detail=False)
    def received(self, request):
        """GET /visits/received/ — incoming requests for *my* listings
        (seller-dashboard.tsx)."""
        qs = self.get_queryset().filter(property__owner=request.user)
        status_param = request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        serializer = VisitRequestSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    def _transition(self, request, pk, new_status):
        visit = get_object_or_404(self.get_queryset(), pk=pk)
        is_landlord = visit.property.owner_id == request.user.id
        is_requester = visit.requester_id == request.user.id
        if not (is_landlord or is_requester or request.user.is_staff):
            return Response(status=403)

        serializer = VisitRequestStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        visit.status = new_status
        note = serializer.validated_data.get("landlord_note")
        if note:
            visit.landlord_note = note
        visit.save(update_fields=["status", "landlord_note", "updated_at"])

        if new_status == VisitRequest.Status.CONFIRMED:
            notify(
                user=visit.requester,
                type=Notification.NotificationType.VISIT_CONFIRMED,
                message=f"Your visit to '{visit.property.title}' was confirmed.",
                link="/buyer-dashboard",
            )
        elif new_status == VisitRequest.Status.CANCELLED:
            other_user = visit.requester if is_landlord else visit.property.owner
            notify(
                user=other_user,
                type=Notification.NotificationType.VISIT_CANCELLED,
                message=f"The visit to '{visit.property.title}' was cancelled.",
                link="/buyer-dashboard",
            )
        return Response(VisitRequestSerializer(visit, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """POST /visits/{id}/confirm/ — landlord accepts the request."""
        return self._transition(request, pk, VisitRequest.Status.CONFIRMED)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """POST /visits/{id}/cancel/ — either side cancels/reschedules."""
        return self._transition(request, pk, VisitRequest.Status.CANCELLED)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """POST /visits/{id}/complete/ — mark a past visit as done."""
        return self._transition(request, pk, VisitRequest.Status.COMPLETED)
