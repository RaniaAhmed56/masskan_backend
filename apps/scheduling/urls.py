from rest_framework.routers import DefaultRouter

from . import views

app_name = "scheduling"

router = DefaultRouter()
router.register("visits", views.VisitRequestViewSet, basename="visit-request")

urlpatterns = router.urls
