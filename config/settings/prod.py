"""Production settings.

Usage: set DJANGO_SETTINGS_MODULE=config.settings.prod on the server /
deployment platform. Every value that differs from `dev.py` is sourced
from the environment — nothing environment-specific is hardcoded here.
"""

import os
from urllib.parse import urlparse

from .base import *  # noqa: F401,F403

DEBUG = False

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
    if host.strip()
]
vercel_host = os.environ.get("VERCEL_URL", "").strip().removeprefix("https://").removeprefix("http://").rstrip("/")
if vercel_host and vercel_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(vercel_host)

# Prefer the connection string commonly exposed by hosted Postgres services,
# while keeping the existing DB_* variables supported.
database_url = os.environ.get("DATABASE_URL")
if database_url:
    parsed_database_url = urlparse(database_url)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed_database_url.path.lstrip("/"),
            "USER": parsed_database_url.username or "",
            "PASSWORD": parsed_database_url.password or "",
            "HOST": parsed_database_url.hostname or "",
            "PORT": str(parsed_database_url.port or 5432),
            "CONN_MAX_AGE": 60,
            "OPTIONS": {"sslmode": "require"},
        }
    }
elif any(os.environ.get(name) for name in ("DB_NAME", "DB_USER", "DB_PASSWORD")):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", ""),
            "USER": os.environ.get("DB_USER", ""),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
            "CONN_MAX_AGE": 60,
        }
    }
else:
    # Allows Vercel to import the application during its build. Configure a
    # hosted Postgres database before sending production traffic.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

CORS_ALLOW_ALL_ORIGINS = False

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "true").lower() == "true"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# In production, point EMAIL_BACKEND at a real provider (SES/SendGrid/etc.)
# via env vars once one is chosen — everything else in the codebase talks
# to apps.common.services.notifications, so this is the only line to change.
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true").lower() == "true"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
    },
}
