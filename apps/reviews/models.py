from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.common.models import TimeStampedModel
from apps.properties.models import Property


class PropertyReview(TimeStampedModel):
    """A guest review on a specific listing — the "Guest Reviews & Ratings"
    block in apartment-details.tsx (separate from AreaReview, which rates
    the neighborhood rather than the unit itself)."""

    property = models.ForeignKey(Property, related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="property_reviews", on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=150, blank=True)
    comment = models.TextField(blank=True)

    class Meta:
        unique_together = ["property", "user"]

    def __str__(self):
        return f"{self.rating}★ on {self.property_id} by {self.user_id}"


class LandlordReview(TimeStampedModel):
    """A tenant reviewing a landlord — landlord-profile.tsx's review list."""

    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="landlord_reviews", on_delete=models.CASCADE
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="written_landlord_reviews", on_delete=models.CASCADE
    )
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="liked_landlord_reviews", blank=True, symmetrical=False
    )

    class Meta:
        unique_together = ["landlord", "reviewer"]

    def __str__(self):
        return f"{self.rating}★ for landlord {self.landlord_id} by {self.reviewer_id}"

    @property
    def like_count(self):
        return self.likes.count()
