from rest_framework import serializers

from apps.accounts.serializers import PublicUserSerializer

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender = PublicUserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ["id", "conversation", "sender", "text", "is_read", "created_at"]
        read_only_fields = ["id", "conversation", "sender", "is_read", "created_at"]


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["text"]


class ConversationSerializer(serializers.ModelSerializer):
    """List-view shape: who the *other* participant is (from the requesting
    user's point of view), plus a last-message preview and unread count —
    exactly what chat.tsx's conversation list needs to render."""

    other_participant = serializers.SerializerMethodField()
    property_title = serializers.CharField(source="property.title", read_only=True, default=None)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["id", "property", "property_title", "other_participant", "last_message", "unread_count", "created_at"]

    def get_other_participant(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        return PublicUserSerializer(obj.other_participant(user)).data if user else None

    def get_last_message(self, obj):
        last = obj.messages.order_by("-created_at").first()
        return MessageSerializer(last).data if last else None

    def get_unread_count(self, obj):
        request = self.context.get("request")
        return obj.unread_count_for(request.user) if request else 0


class ConversationCreateSerializer(serializers.Serializer):
    recipient_id = serializers.IntegerField()
    property_id = serializers.IntegerField(required=False, allow_null=True)
    message = serializers.CharField(required=False, allow_blank=True)
