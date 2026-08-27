from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class Notification(TimeStampedModel):
    """An in-app notification — the bell icon / "Notifications" tab on
    buyer-dashboard.tsx and seller-dashboard.tsx. Deliberately separate
    from `apps.common.services.notifications` (email/SMS): that module
    reaches an outside channel, this model is what the frontend polls to
    render its own notification list/badge.
    """

    class NotificationType(models.TextChoices):
        MESSAGE = "message", "New message"
        VISIT_REQUESTED = "visit_requested", "Visit requested"
        VISIT_CONFIRMED = "visit_confirmed", "Visit confirmed"
        VISIT_CANCELLED = "visit_cancelled", "Visit cancelled"
        LISTING_APPROVED = "listing_approved", "Listing approved"
        LISTING_REJECTED = "listing_rejected", "Listing rejected"
        NEW_REVIEW = "new_review", "New review"
        SYSTEM = "system", "System"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="notifications", on_delete=models.CASCADE)
    type = models.CharField(max_length=30, choices=NotificationType.choices, default=NotificationType.SYSTEM)
    message = models.CharField(max_length=255)
    link = models.CharField(
        max_length=255, blank=True, help_text="Relative frontend route to open on click, e.g. '/chat'."
    )
    is_read = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["user", "is_read"])]

    def __str__(self):
        return f"{self.user_id}: {self.message[:40]}"
