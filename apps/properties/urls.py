from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "properties"

router = DefaultRouter()
router.register("amenities", views.AmenityViewSet, basename="amenity")
router.register("", views.PropertyViewSet, basename="property")

urlpatterns = [
    path("ai-search/", views.AISearchView.as_view(), name="ai-search"),
    path("ai-search/history/", views.AISearchHistoryView.as_view(), name="ai-search-history"),
] + router.urls
