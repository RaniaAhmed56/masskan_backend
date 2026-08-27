from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "subscriptions"

router = DefaultRouter()
router.register("plans", views.SubscriptionPlanViewSet, basename="subscription-plan")

urlpatterns = [
    path("me/", views.MySubscriptionView.as_view(), name="my-subscription"),
    path("subscribe/", views.SubscribeView.as_view(), name="subscribe"),
    path("cancel/", views.CancelSubscriptionView.as_view(), name="cancel"),
] + router.urls
