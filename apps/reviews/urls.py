from django.urls import path

from . import views

app_name = "reviews"

property_reviews = views.PropertyReviewViewSet.as_view({"get": "list", "post": "create"})
property_review_detail = views.PropertyReviewViewSet.as_view({"delete": "destroy"})

landlord_reviews = views.LandlordReviewViewSet.as_view({"get": "list", "post": "create"})
landlord_review_detail = views.LandlordReviewViewSet.as_view({"delete": "destroy"})
landlord_review_like = views.LandlordReviewViewSet.as_view({"post": "like"})

urlpatterns = [
    path("properties/<int:property_id>/reviews/", property_reviews, name="property-review-list"),
    path("properties/<int:property_id>/reviews/<int:pk>/", property_review_detail, name="property-review-detail"),
    path("landlords/<int:landlord_id>/reviews/", landlord_reviews, name="landlord-review-list"),
    path("landlords/<int:landlord_id>/reviews/<int:pk>/", landlord_review_detail, name="landlord-review-detail"),
    path(
        "landlords/<int:landlord_id>/reviews/<int:pk>/like/", landlord_review_like, name="landlord-review-like"
    ),
]
