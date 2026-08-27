"""Stateless, signed tokens for email verification and password reset.

Both build on Django's battle-tested `PasswordResetTokenGenerator` (HMAC of
the user's pk + password hash + a timestamp, so a token automatically
invalidates itself once used to change the password, and expires via
`PASSWORD_RESET_TIMEOUT`). We encode the user pk alongside the token into a
single opaque string so the API surface is just "one token param", matching
how the frontend's reset-password.tsx / verified-password.tsx pages already
expect a single `?token=` query param.
"""

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{timestamp}{user.is_email_verified}"


password_reset_token_generator = PasswordResetTokenGenerator()
email_verification_token_generator = EmailVerificationTokenGenerator()


def _encode(user, generator: PasswordResetTokenGenerator) -> str:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = generator.make_token(user)
    return f"{uid}.{token}"


def _decode(token: str, generator: PasswordResetTokenGenerator, user_model):
    try:
        uid_b64, raw_token = token.split(".", 1)
        uid = force_str(urlsafe_base64_decode(uid_b64))
        user = user_model.objects.get(pk=uid)
    except (ValueError, TypeError, OverflowError, user_model.DoesNotExist):
        return None
    if not generator.check_token(user, raw_token):
        return None
    return user


def make_password_reset_token(user) -> str:
    return _encode(user, password_reset_token_generator)


def make_email_verification_token(user) -> str:
    return _encode(user, email_verification_token_generator)


def resolve_password_reset_token(token: str):
    from .models import User

    return _decode(token, password_reset_token_generator, User)


def resolve_email_verification_token(token: str):
    from .models import User

    return _decode(token, email_verification_token_generator, User)
