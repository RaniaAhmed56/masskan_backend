from django.db.models import Avg, Count, FloatField, Q
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.common.permissions import IsAdminRole
from apps.common.services.notifications import send_email_verification, send_password_reset_email

from .models import User, VerificationDocument
from .serializers import (
    ChangePasswordSerializer,
    EmailVerificationConfirmSerializer,
    MasskanTokenObtainPairSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PublicLandlordSerializer,
    RegisterSerializer,
    UserSerializer,
    VerificationDocumentReviewSerializer,
    VerificationDocumentSerializer,
)
from .tokens import resolve_email_verification_token, resolve_password_reset_token


class RegisterView(generics.CreateAPIView):
    """POST /api/accounts/register/

    Public. Creates the account and immediately fires a (stubbed, see
    apps.common.services.notifications) verification email — mirrors
    signup.tsx's single-step "Create Your Account" form.
    """

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_email_verification(user)

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class MasskanTokenObtainPairView(TokenObtainPairView):
    """POST /api/accounts/login/ — email + password -> {access, refresh, user}."""

    serializer_class = MasskanTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    """POST /api/accounts/logout/ {refresh: "..."} — blacklists the refresh
    token so it can't be used again (requires the token_blacklist app,
    already enabled in INSTALLED_APPS)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response({"detail": "refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            RefreshToken(refresh).blacklist()
        except Exception:  # noqa: BLE001 — already-blacklisted/invalid tokens are a no-op
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/accounts/me/ — the logged-in user's own profile.

    Backs profile.tsx's editable profile fields for both account roles.
    """

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """POST /api/accounts/me/change-password/ — logged-in password change."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response({"old_password": "Incorrect password."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Password updated."})


class PasswordResetRequestView(APIView):
    """POST /api/accounts/password-reset/ {email} — always 200s (never
    reveals whether an email exists) and, if it does, fires a reset email.
    Backs the "Forgot?" link on signin.tsx."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(email__iexact=serializer.validated_data["email"])
            send_password_reset_email(user)
        except User.DoesNotExist:
            pass
        return Response({"detail": "If that email exists, a reset link has been sent."})


class PasswordResetConfirmView(APIView):
    """POST /api/accounts/password-reset/confirm/ {token, new_password}
    Backs reset-password.tsx."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = resolve_password_reset_token(serializer.validated_data["token"])
        if user is None:
            return Response({"token": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Password has been reset."})


class ResendEmailVerificationView(APIView):
    """POST /api/accounts/verify-email/resend/ — logged-in user requests a
    fresh verification link."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.is_email_verified:
            return Response({"detail": "Email is already verified."})
        send_email_verification(request.user)
        return Response({"detail": "Verification email sent."})


class EmailVerificationConfirmView(APIView):
    """POST /api/accounts/verify-email/confirm/ {token}
    Backs verified-password.tsx's email-confirmation step."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = EmailVerificationConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = resolve_email_verification_token(serializer.validated_data["token"])
        if user is None:
            return Response({"token": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])
        return Response({"detail": "Email verified."})


class PublicLandlordDetailView(generics.RetrieveAPIView):
    """GET /api/accounts/landlords/{id}/ — public landlord-profile.tsx data:
    identity + rating/review/listing aggregates."""

    serializer_class = PublicLandlordSerializer
    permission_classes = [permissions.AllowAny]
    lookup_url_kwarg = "user_id"

    def get_queryset(self):
        from apps.properties.models import Property
        from apps.reviews.models import LandlordReview

        return User.objects.filter(role__in=[User.Role.LANDLORD, User.Role.BOTH]).annotate(
            average_rating=Coalesce(
                Avg("landlord_reviews__rating", filter=Q(landlord_reviews__isnull=False)),
                0.0,
                output_field=FloatField(),
            ),
            review_count=Count("landlord_reviews", distinct=True),
            active_listing_count=Count(
                "properties", filter=Q(properties__status=Property.Status.ACTIVE), distinct=True
            ),
        )


class VerificationDocumentViewSet(viewsets.ModelViewSet):
    """/api/accounts/verification-documents/

    - Regular users: list/create/retrieve their own documents (profile.tsx
      "Verification Documents" upload sections).
    - Admins: list *all* pending documents and approve/reject them
      (admin-dashboard.tsx moderation queue) via the extra `review` action.
    """

    serializer_class = VerificationDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff and self.request.query_params.get("all") == "true":
            return VerificationDocument.objects.select_related("user").all()
        return VerificationDocument.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_permissions(self):
        if self.action == "review":
            return [IsAdminRole()]
        return super().get_permissions()

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        document = get_object_or_404(VerificationDocument, pk=pk)
        serializer = VerificationDocumentReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]

        document.status = (
            VerificationDocument.Status.APPROVED if action == "approve" else VerificationDocument.Status.REJECTED
        )
        document.rejection_reason = serializer.validated_data.get("rejection_reason", "")
        document.reviewed_by = request.user
        document.reviewed_at = timezone.now()
        document.save()

        # If every document for this user is now approved, flip their
        # overall verification_status — drives the "Verified" badge shown
        # across profile.tsx / landlord-profile.tsx / property cards.
        owner = document.user
        docs = owner.verification_documents.all()
        if docs.exists() and all(d.status == VerificationDocument.Status.APPROVED for d in docs):
            owner.verification_status = User.VerificationStatus.VERIFIED
            owner.save(update_fields=["verification_status"])
        elif document.status == VerificationDocument.Status.REJECTED:
            owner.verification_status = User.VerificationStatus.REJECTED
            owner.save(update_fields=["verification_status"])

        return Response(VerificationDocumentSerializer(document).data)
