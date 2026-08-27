from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = "accounts"

router = DefaultRouter()
router.register("verification-documents", views.VerificationDocumentViewSet, basename="verification-document")

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.MasskanTokenObtainPairView.as_view(), name="login"),
    path("login/refresh/", TokenRefreshView.as_view(), name="login-refresh"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("me/", views.MeView.as_view(), name="me"),
    path("me/change-password/", views.ChangePasswordView.as_view(), name="change-password"),
    path("password-reset/", views.PasswordResetRequestView.as_view(), name="password-reset"),
    path("password-reset/confirm/", views.PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("verify-email/resend/", views.ResendEmailVerificationView.as_view(), name="verify-email-resend"),
    path("verify-email/confirm/", views.EmailVerificationConfirmView.as_view(), name="verify-email-confirm"),
    path("landlords/<int:user_id>/", views.PublicLandlordDetailView.as_view(), name="landlord-detail"),
] + router.urls
