from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


def property_image_upload_path(instance, filename):
    return f"properties/{instance.property_id}/{filename}"


class Amenity(models.Model):
    """Seeded lookup table — keys mirror the frontend's
    `src/app/lib/amenity-icons.tsx` map 1:1 so the same `key` string picks
    the right icon on both ends without a translation layer.
    """

    key = models.SlugField(max_length=30, unique=True)
    label = models.CharField(max_length=50)

    class Meta:
        verbose_name_plural = "amenities"
        ordering = ["label"]

    def __str__(self):
        return self.label


class Property(TimeStampedModel):
    """A single listing. Field set mirrors what search-results.tsx,
    apartment-details.tsx, add-listing.tsx and the AI search flow all
    read/write, so nothing on the frontend needs a shape it can't get.
    """

    class PropertyType(models.TextChoices):
        APARTMENT = "apartment", "Apartment"
        PENTHOUSE = "penthouse", "Penthouse"
        STUDIO = "studio", "Studio"
        VILLA = "villa", "Villa"
        LOFT = "loft", "Loft"
        TOWNHOUSE = "townhouse", "Townhouse"

    class Furnished(models.TextChoices):
        FURNISHED = "furnished", "Furnished"
        UNFURNISHED = "unfurnished", "Unfurnished"
        SEMI = "semi", "Semi-Furnished"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Review"
        ACTIVE = "active", "Active"
        REJECTED = "rejected", "Rejected"
        ARCHIVED = "archived", "Archived"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="properties", on_delete=models.CASCADE)

    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    property_type = models.CharField(max_length=12, choices=PropertyType.choices, default=PropertyType.APARTMENT)

    price = models.DecimalField(max_digits=10, decimal_places=2)

    bedrooms = models.PositiveSmallIntegerField(default=1)
    bathrooms = models.PositiveSmallIntegerField(default=1)
    area_sqft = models.PositiveIntegerField(help_text="Floor area in square feet.")
    floor = models.PositiveSmallIntegerField(null=True, blank=True)

    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    area_name = models.CharField(
        max_length=100, blank=True, help_text="Neighborhood name — matches apps.areas.Area.name when set."
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    near_public_transport = models.BooleanField(default=False)

    furnished = models.CharField(max_length=11, choices=Furnished.choices, default=Furnished.UNFURNISHED)
    pet_friendly = models.BooleanField(default=False)
    amenities = models.ManyToManyField(Amenity, related_name="properties", blank=True)

    available_from = models.DateField(null=True, blank=True)
    lease_term_months = models.PositiveSmallIntegerField(null=True, blank=True)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    rejection_reason = models.CharField(max_length=255, blank=True)
    is_featured = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "properties"
        indexes = [
            models.Index(fields=["status", "city"]),
            models.Index(fields=["status", "property_type"]),
            models.Index(fields=["status", "price"]),
        ]

    def __str__(self):
        return self.title

    @property
    def area_m2(self) -> int:
        """Convenience conversion — apartment-details.tsx shows both units."""
        return round(self.area_sqft * 0.0929)

    @property
    def average_rating(self):
        return self.reviews.aggregate(models.Avg("rating"))["rating__avg"] or 0

    @property
    def review_count(self):
        return self.reviews.count()


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to=property_image_upload_path)
    order = models.PositiveSmallIntegerField(default=0)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"Image #{self.order} for {self.property_id}"


class Favorite(TimeStampedModel):
    """A searcher saving a listing — powers the heart icon everywhere plus
    profile.tsx / buyer-dashboard.tsx "Saved" tabs."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="favorites", on_delete=models.CASCADE)
    property = models.ForeignKey(Property, related_name="favorited_by", on_delete=models.CASCADE)

    class Meta:
        unique_together = ["user", "property"]

    def __str__(self):
        return f"{self.user_id} ♥ {self.property_id}"


class AISearchLog(TimeStampedModel):
    """A record of one AI-search-questionnaire submission (ai-search-
    questionnaire.tsx) and the criteria used, for basic usage analytics and
    so a signed-in user's last search can be recalled later. Anonymous
    submissions are allowed (`user` nullable) since the frontend lets a
    visitor try the questionnaire before signing up.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, related_name="ai_search_logs", on_delete=models.SET_NULL
    )
    criteria = models.JSONField(help_text="Raw questionnaire answers as submitted by the frontend.")
    result_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"AI search #{self.pk} ({self.result_count} matches)"
