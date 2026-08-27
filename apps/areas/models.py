from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.common.models import TimeStampedModel


class Area(models.Model):
    """A neighborhood — backs the "Neighborhood Insights" panel
    (area-rating.tsx) shown on apartment-details.tsx. `name` is matched
    against `Property.area_name` by the frontend/detail view, not a FK,
    since a property is free-text about its neighborhood at listing time.
    """

    class PriceLevel(models.TextChoices):
        LOW = "low", "Low"
        MODERATE = "moderate", "Moderate"
        HIGH = "high", "High"

    name = models.CharField(max_length=100, unique=True)
    city = models.CharField(max_length=100, blank=True)

    safety = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)], default=0)
    quietness = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)], default=0)
    amenities_score = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)], default=0)
    transport = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)], default=0)
    schools = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)], default=0)
    entertainment = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)], default=0)
    family_friendly_score = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)], default=0)
    student_friendly_score = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)], default=0)

    price_level = models.CharField(max_length=8, choices=PriceLevel.choices, default=PriceLevel.MODERATE)
    avg_price_min = models.PositiveIntegerField(null=True, blank=True, help_text="Avg. 2BR monthly rent, low end.")
    avg_price_max = models.PositiveIntegerField(null=True, blank=True, help_text="Avg. 2BR monthly rent, high end.")
    demand_trend = models.CharField(
        max_length=100, blank=True, help_text="e.g. '+12% demand growth this month'."
    )

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "areas"

    def __str__(self):
        return self.name

    @property
    def average_rating(self):
        return self.reviews.aggregate(models.Avg("rating"))["rating__avg"] or 0

    @property
    def review_count(self):
        return self.reviews.count()


class NearbyPlace(models.Model):
    class Category(models.TextChoices):
        TRANSPORT = "transport", "Transport"
        SHOPPING = "shopping", "Shopping"
        EDUCATION = "education", "Education"
        HEALTHCARE = "healthcare", "Healthcare"
        RECREATION = "recreation", "Recreation"

    area = models.ForeignKey(Area, related_name="nearby_places", on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=12, choices=Category.choices, default=Category.SHOPPING)
    distance_label = models.CharField(max_length=50, help_text="e.g. '5 min walk', '10 min'.")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.name} ({self.area.name})"


class AreaReview(TimeStampedModel):
    area = models.ForeignKey(Area, related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="area_reviews", on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)

    class Meta:
        unique_together = ["area", "user"]

    def __str__(self):
        return f"{self.rating}★ on {self.area.name} by {self.user_id}"

    @property
    def helpful_count(self):
        return self.helpful_votes.count()


class AreaReviewHelpfulVote(models.Model):
    """Through-table for the "Helpful (N)" toggle button in area-rating.tsx —
    one vote per user per review, so the count is real instead of a client-
    side-only increment."""

    review = models.ForeignKey(AreaReview, related_name="helpful_votes", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        unique_together = ["review", "user"]
