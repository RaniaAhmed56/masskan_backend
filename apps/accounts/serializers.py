from django.contrib.auth import password_validation
from django.contrib.auth.models import update_last_login
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, VerificationDocument


class UserSerializer(serializers.ModelSerializer):
    """The authenticated user's own profile — GET/PATCH /api/accounts/me/."""

    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "phone",
            "avatar",
            "bio",
            "company_name",
            "response_time_minutes",
            "is_email_verified",
            "verification_status",
            "is_staff",
            "date_joined",
        ]
        read_only_fields = ["id", "email", "is_email_verified", "verification_status", "is_staff", "date_joined"]


class PublicUserSerializer(serializers.ModelSerializer):
    """Trimmed-down public view of a user — used wherever another user's
    identity is embedded (property owner on a listing, message sender,
    review author, etc.) so we never leak email/phone/bio to strangers.
    """

    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ["id", "full_name", "avatar", "role"]


class PublicLandlordSerializer(serializers.ModelSerializer):
    """Public landlord-profile page (landlord-profile.tsx): identity +
    the aggregate stats the frontend needs, without exposing private data.
    Aggregate fields are annotated onto the queryset by the view.
    """

    full_name = serializers.ReadOnlyField()
    average_rating = serializers.FloatField(read_only=True, default=0)
    review_count = serializers.IntegerField(read_only=True, default=0)
    active_listing_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "avatar",
            "bio",
            "company_name",
            "response_time_minutes",
            "verification_status",
            "date_joined",
            "average_rating",
            "review_count",
            "active_listing_count",
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "phone", "role", "password", "password_confirm"]

    def validate_role(self, value):
        if value == User.Role.BOTH:
            # Registration only offers the two primary roles (matches the
            # signup.tsx "Apartment Seeker" / "Property Owner" choice) —
            # `both` is set later if/when a user opts into the other side.
            raise serializers.ValidationError("Choose either 'searcher' or 'landlord' when signing up.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        password_validation.validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        # username is required by AbstractUser; derive one from the email
        # local-part since the frontend never collects a separate username.
        base_username = validated_data["email"].split("@")[0]
        username = base_username
        suffix = 1
        while User.objects.filter(username=username).exists():
            suffix += 1
            username = f"{base_username}{suffix}"
        user = User(username=username, **validated_data)
        user.set_password(password)
        user.save()
        return user


class MasskanTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds the user payload to the login response so the frontend doesn't
    need a second round-trip to /api/accounts/me/ right after signing in."""

    def validate(self, attrs):
        data = super().validate(attrs)
        update_last_login(None, self.user)
        data["user"] = UserSerializer(self.user, context=self.context).data
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        password_validation.validate_password(value, self.context["request"].user)
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)


class EmailVerificationConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()


class VerificationDocumentSerializer(serializers.ModelSerializer):
    """`user_id`/`user_full_name`/`user_email` are only meaningful on the
    admin moderation queue (GET ?all=true — admin-dashboard.tsx); they're
    harmless no-ops on a user's own document list."""

    user_id = serializers.IntegerField(source="user.id", read_only=True)
    user_full_name = serializers.CharField(source="user.full_name", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = VerificationDocument
        fields = [
            "id",
            "doc_type",
            "file",
            "status",
            "rejection_reason",
            "created_at",
            "reviewed_at",
            "user_id",
            "user_full_name",
            "user_email",
        ]
        read_only_fields = ["id", "status", "rejection_reason", "created_at", "reviewed_at"]


class VerificationDocumentReviewSerializer(serializers.Serializer):
    """Admin action: approve or reject a pending document."""

    action = serializers.ChoiceField(choices=["approve", "reject"])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
