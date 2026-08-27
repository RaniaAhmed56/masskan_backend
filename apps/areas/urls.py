from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "areas"

router = DefaultRouter()
router.register("", views.AreaViewSet, basename="area")

urlpatterns = [
    path("reviews/<int:review_id>/helpful/", views.AreaReviewHelpfulView.as_view(), name="review-helpful"),
] + router.urls
