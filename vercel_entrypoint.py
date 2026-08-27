"""Explicit WSGI entrypoint for Vercel's Python runtime."""

import os

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.prod"

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()