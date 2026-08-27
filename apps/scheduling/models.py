import builtins

from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.properties.models import Property


class VisitRequest(TimeStampedModel):
    """A tour-booking request — backs schedule.tsx (the booking form) and the
    "Visits" tab of buyer-dashboard.tsx / the visit-requests list a landlord
    sees on seller-dashboard.tsx.

    `full_name`/`email`/`phone` are captured as a snapshot of the booking
    form at submit time (the frontend form collects them even for a logged-in
    user, e.g. to confirm contact details), separate from the `requester`
    account fields which may change later.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    property = models.ForeignKey(Property, related_name="visit_requests", on_delete=models.CASCADE)
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="visit_requests", on_delete=models.CASCADE
    )

    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30)

    visit_date = models.DateField()
    visit_time = models.TimeField()
    notes = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    landlord_note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["visit_date", "visit_time"]
        indexes = [models.Index(fields=["status", "visit_date"])]

    def __str__(self):
        return f"Visit #{self.pk} — {self.property_id} on {self.visit_date} ({self.status})"

    # NOTE: the standard `@property` decorator can't be used here — this
    # class already has a field literally named `property` (the FK to the
    # listing), which shadows the `property` builtin inside the class body.
    @builtins.property
    def landlord(self):
        return self.property.owner
