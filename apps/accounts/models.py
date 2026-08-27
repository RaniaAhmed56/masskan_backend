from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.common.models import TimeStampedModel


def avatar_upload_path(instance, filename):
    return f"avatars/{instance.pk or 'new'}/{filename}"


def verification_doc_upload_path(instance, filename):
    return f"verification_docs/{instance.user_id}/{filename}"


class User(AbstractUser):
    """Custom user model — the single source of truth for "which kind of
    account is this" across the whole API (search filters, permissions,
    dashboards all key off `role`).

    Mirrors the frontend's `userType: 'landlord' | 'searcher' | 'both'`
    (see src/app/App.tsx `User` interface) so the two stay in lockstep.
    """

    class Role(models.TextChoices):
        SEARCHER = "searcher", "Apartment Seeker"
        LANDLORD = "landlord", "Property Owner"
        BOTH = "both", "Both"

    class VerificationStatus(models.TextChoices):
        UNVERIFIED = "unverified", "Unverified"
        PENDING = "pending", "Pending Review"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"

    # AbstractUser already provides: username, first_name, last_name, email,
    # is_staff, is_active, date_joined, password, etc. We require+unique the
    # email since it's the real login identifier the frontend uses.
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.SEARCHER)

    phone = models.CharField(max_length=32, blank=True)
    avatar = models.ImageField(upload_to=avatar_upload_path, null=True, blank=True)
    bio = models.TextField(blank=True)

    # Landlord-facing "about" fields shown on the public landlord-profile page.
    company_name = models.CharField(max_length=150, blank=True)
    response_time_minutes = models.PositiveIntegerField(
        null=True, blank=True, help_text="Typical response time, shown as e.g. 'Usually within 2 hours'."
    )

    is_email_verified = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=10, choices=VerificationStatus.choices, default=VerificationStatus.UNVERIFIED
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def is_landlord(self) -> bool:
        return self.role in (self.Role.LANDLORD, self.Role.BOTH)

    @property
    def is_searcher(self) -> bool:
        return self.role in (self.Role.SEARCHER, self.Role.BOTH)


class VerificationDocument(TimeStampedModel):
    """An uploaded ID / proof-of-income / business-license document.

    Matches the "Verification Documents" sections on both the searcher and
    landlord variants of profile.tsx. `doc_type` is intentionally a single
    shared enum (not split per-role) since the moderation flow — pending /
    approved / rejected, reviewed in admin-dashboard.tsx — is identical
    either way; the frontend just shows a different subset of choices per
    role.
    """

    class DocType(models.TextChoices):
        ID_CARD = "id_card", "National ID / Passport"
        DRIVERS_LICENSE = "drivers_license", "Driver's License"
        PROOF_OF_INCOME = "proof_of_income", "Proof of Income"
        EMPLOYMENT_LETTER = "employment_letter", "Employment Letter"
        BUSINESS_LICENSE = "business_license", "Business License"
        PROPERTY_DEED = "property_deed", "Property Ownership Deed"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(User, related_name="verification_documents", on_delete=models.CASCADE)
    doc_type = models.CharField(max_length=20, choices=DocType.choices)
    file = models.FileField(upload_to=verification_doc_upload_path)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    rejection_reason = models.CharField(max_length=255, blank=True)
    reviewed_by = models.ForeignKey(
        User, null=True, blank=True, related_name="reviewed_documents", on_delete=models.SET_NULL
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_doc_type_display()} — {self.user.email} ({self.status})"
