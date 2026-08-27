from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.properties.models import Property


class Conversation(TimeStampedModel):
    """A message thread between two users, usually about one property —
    backs chat.tsx. `property` is nullable so a conversation can also start
    from a landlord's public profile without a specific listing in context.
    """

    property = models.ForeignKey(
        Property, null=True, blank=True, related_name="conversations", on_delete=models.SET_NULL
    )
    initiator = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="conversations_started", on_delete=models.CASCADE
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="conversations_received", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ["property", "initiator", "recipient"]

    def __str__(self):
        return f"Conversation #{self.pk}: {self.initiator_id} ↔ {self.recipient_id}"

    def other_participant(self, user):
        return self.recipient if user == self.initiator else self.initiator

    def unread_count_for(self, user):
        return self.messages.filter(is_read=False).exclude(sender=user).count()


class Message(TimeStampedModel):
    conversation = models.ForeignKey(Conversation, related_name="messages", on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="sent_messages", on_delete=models.CASCADE)
    text = models.TextField()
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message #{self.pk} in conversation #{self.conversation_id}"
