from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """/api/v1/notifications/ — the Notifications tab + bell badge on
    buyer-dashboard.tsx / seller-dashboard.tsx."""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False)
    def unread_count(self, request):
        """GET /notifications/unread_count/ — powers the bell badge number."""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"unread_count": count})

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        """POST /notifications/{id}/read/ — mark a single notification read."""
        notification = get_object_or_404(self.get_queryset(), pk=pk)
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read", "updated_at"])
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=["post"])
    def read_all(self, request):
        """POST /notifications/read_all/ — "mark all as read"."""
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"marked_read": updated})
