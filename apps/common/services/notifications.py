"""Single call site for every outbound email/SMS the backend sends.

Nothing else in the codebase should call `django.core.mail.send_mail`
directly — routing everything through here means swapping providers
(console -> SES/SendGrid, or adding SMS via Twilio) is a one-file change.

In dev/test, `EMAIL_BACKEND` is the console backend (see settings/dev.py),
so these calls just print to stdout — no external service required to run
the project locally.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_transactional_email(*, to: str, subject: str, message: str) -> None:
    """Send a single plain-text transactional email.

    Swallows send failures into a log line rather than raising, so a flaky
    email provider never turns into a 500 on a signup/booking endpoint —
    the triggering action (account creation, visit request, etc.) still
    succeeds even if the notification email doesn't go out.
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to],
            fail_silently=False,
        )
    except Exception:  # noqa: BLE001 — deliberately broad, see docstring
        logger.exception("Failed to send email to %s (subject=%r)", to, subject)


def send_email_verification(user) -> None:
    from apps.accounts.tokens import make_email_verification_token

    token = make_email_verification_token(user)
    link = f"{settings.FRONTEND_BASE_URL}/signin?verify_token={token}"
    send_transactional_email(
        to=user.email,
        subject="Verify your Masskan account",
        message=(
            f"Hi {user.first_name or user.username},\n\n"
            f"Please confirm your email address by visiting:\n{link}\n\n"
            "If you didn't create a Masskan account, you can ignore this email."
        ),
    )


def send_password_reset_email(user) -> None:
    from apps.accounts.tokens import make_password_reset_token

    token = make_password_reset_token(user)
    link = f"{settings.FRONTEND_BASE_URL}/verified-password?token={token}"
    send_transactional_email(
        to=user.email,
        subject="Reset your Masskan password",
        message=(
            f"Hi {user.first_name or user.username},\n\n"
            f"Reset your password by visiting:\n{link}\n\n"
            "This link expires in 1 hour. If you didn't request this, you can ignore this email."
        ),
    )


def send_sms(*, to: str, message: str) -> None:
    """Placeholder for SMS notifications (e.g. visit reminders).

    No SMS provider is wired up yet — this just logs so call sites can be
    written now and start actually sending the moment a provider (Twilio,
    Vonage, etc.) is chosen and its credentials land in `.env`.
    """
    logger.info("[SMS stub] to=%s message=%r", to, message)
