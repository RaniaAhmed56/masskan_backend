from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base class adding self-updating `created_at` / `updated_at`.

    Every model in the project inherits from this instead of redefining
    the same two fields — keeps `created_at`/`updated_at` semantics (and
    default ordering) consistent across all sixteen-odd domain models.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]
