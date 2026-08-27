"""Single call site for creating in-app notifications, mirroring the pattern
used by `apps.common.services.notifications` for email/SMS. Other apps
(scheduling, messaging, properties, reviews) call `notify()` instead of
creating `Notification` rows directly, so the in-app notification shape
stays consistent everywhere it's triggered from.
"""

from .models import Notification


def notify(*, user, type, message, link=""):
    if user is None:
        return None
    return Notification.objects.create(user=user, type=type, message=message, link=link)
