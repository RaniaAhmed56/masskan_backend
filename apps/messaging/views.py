from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.models import User
from apps.notifications.models import Notification
from apps.notifications.services import notify
from apps.properties.models import Property

from .models import Conversation
from .serializers import ConversationCreateSerializer, ConversationSerializer, MessageCreateSerializer, MessageSerializer


class ConversationViewSet(viewsets.ModelViewSet):
    """/api/v1/messaging/conversations/ — chat.tsx.

    Only `list`, `create` (start-or-fetch a thread) and the nested
    `messages` action are exposed; conversations aren't edited or deleted,
    only appended to.
    """

    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        return (
            Conversation.objects.filter(models.Q(initiator=user) | models.Q(recipient=user))
            .select_related("initiator", "recipient", "property")
            .order_by("-updated_at")
        )

    def create(self, request, *args, **kwargs):
        """POST {recipient_id, property_id?, message?} — finds-or-creates
        the thread and, if `message` is given, sends it immediately. This
        is the single call chat.tsx needs when a user hits "Contact" from
        apartment-details.tsx."""
        serializer = ConversationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        recipient = get_object_or_404(User, pk=data["recipient_id"])
        property_obj = None
        if data.get("property_id"):
            property_obj = get_object_or_404(Property, pk=data["property_id"])

        conversation, _created = Conversation.objects.get_or_create(
            property=property_obj,
            initiator=request.user,
            recipient=recipient,
        )
        if data.get("message"):
            conversation.messages.create(sender=request.user, text=data["message"])
            conversation.save(update_fields=["updated_at"])
            notify(
                user=conversation.other_participant(request.user),
                type=Notification.NotificationType.MESSAGE,
                message=f"New message from {request.user.full_name}.",
                link="/chat",
            )

        return Response(ConversationSerializer(conversation, context={"request": request}).data, status=201)

    @action(detail=True, methods=["get", "post"])
    def messages(self, request, pk=None):
        conversation = self.get_object()
        if request.method == "GET":
            # Opening the thread marks the other participant's messages read.
            conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
            serializer = MessageSerializer(conversation.messages.select_related("sender"), many=True)
            return Response(serializer.data)

        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = conversation.messages.create(sender=request.user, **serializer.validated_data)
        conversation.save(update_fields=["updated_at"])
        notify(
            user=conversation.other_participant(request.user),
            type=Notification.NotificationType.MESSAGE,
            message=f"New message from {request.user.full_name}.",
            link="/chat",
        )
        return Response(MessageSerializer(message).data, status=201)
