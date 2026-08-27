"""
Root URL configuration.

Every app mounts its own `urls.py` under a versioned `/api/v1/<app>/`
prefix — see each app's urls.py for its endpoint list, and README.md for
the full documented reference. `/api/v1/` (no further path) is intentionally
left unbound; discovery of available resources happens via the README, not
a self-describing root — keeps this file a flat, readable table of contents.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/accounts/", include("apps.accounts.urls")),
    path("api/v1/properties/", include("apps.properties.urls")),
    path("api/v1/messaging/", include("apps.messaging.urls")),
    path("api/v1/scheduling/", include("apps.scheduling.urls")),
    path("api/v1/reviews/", include("apps.reviews.urls")),
    path("api/v1/areas/", include("apps.areas.urls")),
    path("api/v1/subscriptions/", include("apps.subscriptions.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
