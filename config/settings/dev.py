"""Local development settings.

Usage: DJANGO_SETTINGS_MODULE=config.settings.dev (this is the default set
in manage.py, so `python manage.py runserver` just works out of the box).
"""

import os

from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# SQLite is enough for local development — zero setup required. Point
# DATABASE_URL at Postgres (see prod.py) for anything beyond a laptop.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Looser CORS in dev so the Vite dev server (random ports during `npm run dev`)
# never gets blocked while iterating locally.
CORS_ALLOW_ALL_ORIGINS = True

# Django Debug Toolbar / extra logging can be added here later without
# touching base.py or prod.py.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO")},
}
