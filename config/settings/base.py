"""
Base Django settings for the Masskan backend, shared by every environment.

Environment-specific overrides live in `dev.py` and `prod.py`. Nothing in
this file should read secrets directly — everything sensitive is pulled
from the environment via `django-environ`-style `os.environ.get()` calls
with safe local-development defaults, so the same codebase runs unchanged
across dev, staging and production simply by swapping env vars.
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths & environment
# ---------------------------------------------------------------------------
# base.py -> settings/ -> config/ -> <project root>
BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-dev-key-change-me")

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "corsheaders",
]

LOCAL_APPS = [
    "apps.common",
    "apps.accounts",
    "apps.properties",
    "apps.messaging",
    "apps.scheduling",
    "apps.reviews",
    "apps.areas",
    "apps.subscriptions",
    "apps.notifications",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Cairo"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static & media files
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardResultsPagination",
    "PAGE_SIZE": 12,
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DATETIME_FORMAT": "iso-8601",
    "EXCEPTION_HANDLER": "apps.common.exceptions.masskan_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# ---------------------------------------------------------------------------
# CORS — the React frontend (Vite dev server + deployed origin) needs access
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = []
for configured_origin in os.environ.get(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:4173,http://localhost:3000"
).split(","):
    configured_origin = configured_origin.strip().rstrip("/")
    if configured_origin and configured_origin not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(configured_origin)

for configured_origin in (
    os.environ.get("FRONTEND_URL", ""),
    os.environ.get("FRONTEND_BASE_URL", ""),
):
    configured_origin = configured_origin.strip().rstrip("/")
    if configured_origin and configured_origin not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(configured_origin)

CORS_ALLOWED_ORIGIN_REGEXES = [
    regex.strip()
    for regex in os.environ.get("CORS_ALLOWED_ORIGIN_REGEXES", "").split(",")
    if regex.strip()
]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS.copy()

# ---------------------------------------------------------------------------
# Email — stubbed to the console by default. Swap EMAIL_BACKEND for a real
# provider (SendGrid, SES, Mailgun...) in prod.py / .env once one is chosen.
# See apps/common/services/notifications.py for the single call site.
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "no-reply@masskan.app")

# ---------------------------------------------------------------------------
# Frontend base URL — used to build links inside emails (verification,
# password reset, etc.) that point back at the React app.
# ---------------------------------------------------------------------------
FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "http://localhost:5173")

# ---------------------------------------------------------------------------
# Masskan-specific tunables
# ---------------------------------------------------------------------------
MAX_PROPERTY_IMAGES = 12
AI_MATCH_RESULTS_LIMIT = 20
