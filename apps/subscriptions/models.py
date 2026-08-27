from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class SubscriptionPlan(TimeStampedModel):
    """A pricing tier — backs pricing-plans.tsx. Both the "seller" (landlord)
    and "buyer" (searcher) tabs on that page read from this same table,
    distinguished by `role`.
    """

    class Role(models.TextChoices):
        LANDLORD = "landlord", "Landlord"
        SEARCHER = "searcher", "Searcher"

    role = models.CharField(max_length=20, choices=Role.choices)
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=60, unique=True)
    price_monthly = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.CharField(max_length=150, blank=True)
    icon = models.CharField(
        max_length=40, blank=True, help_text="lucide-react icon name, e.g. 'Rocket', 'Crown'."
    )
    is_popular = models.BooleanField(default=False)
    sort_order = models.PositiveSmallIntegerField(default=0)

    # Plan limits referenced by the frontend copy (listings cap, contact
    # quota, etc.) — kept as plain integers rather than parsed from feature
    # text so the frontend/backend agree on the actual enforced number.
    max_active_listings = models.PositiveIntegerField(null=True, blank=True, help_text="Landlord plans only. Blank = unlimited.")
    max_saved_properties = models.PositiveIntegerField(null=True, blank=True, help_text="Searcher plans only. Blank = unlimited.")
    max_landlord_contacts_per_month = models.PositiveIntegerField(
        null=True, blank=True, help_text="Searcher plans only. Blank = unlimited."
    )
    has_ai_matching = models.BooleanField(default=False)
    has_priority_support = models.BooleanField(default=False)

    class Meta:
        ordering = ["role", "sort_order"]

    def __str__(self):
        return f"{self.name} ({self.role})"


class PlanFeature(TimeStampedModel):
    """One bullet row in a pricing card, e.g. {"Featured badge", included:
    False} — kept as data rather than hard-coded frontend copy so an admin
    can edit pricing-page copy without a deploy."""

    plan = models.ForeignKey(SubscriptionPlan, related_name="features", on_delete=models.CASCADE)
    text = models.CharField(max_length=150)
    included = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.text


class Subscription(TimeStampedModel):
    """A user's subscription to a plan. Payment collection itself is out of
    scope for now (see `apps.subscriptions.services.payments` — a stub
    interface, wired for a real provider like Stripe/Paymob later); this
    model just tracks the resulting state.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="subscriptions", on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, related_name="subscriptions", on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    started_at = models.DateTimeField(auto_now_add=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # Populated by whichever PaymentProvider implementation handled this
    # subscription — a stub id for now, a real charge/subscription id once
    # a provider is wired in.
    payment_provider = models.CharField(max_length=30, default="stub")
    external_reference = models.CharField(max_length=100, blank=True)

    class Meta:
        indexes = [models.Index(fields=["user", "status"])]

    def __str__(self):
        return f"{self.user_id} → {self.plan.name} ({self.status})"
