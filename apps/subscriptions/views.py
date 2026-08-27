from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Subscription, SubscriptionPlan
from .serializers import SubscribeRequestSerializer, SubscriptionPlanSerializer, SubscriptionSerializer
from .services.payments import get_payment_provider


class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/v1/subscriptions/plans/?role=landlord|searcher — the cards
    on pricing-plans.tsx."""

    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        qs = SubscriptionPlan.objects.prefetch_related("features")
        role = self.request.query_params.get("role")
        if role:
            qs = qs.filter(role=role)
        return qs


class MySubscriptionView(APIView):
    """GET /api/v1/subscriptions/me/ — the current user's active
    subscription, or null. Used to show the "Current Plan" state on
    pricing-plans.tsx and to gate plan-limited actions elsewhere."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        subscription = (
            Subscription.objects.filter(user=request.user, status=Subscription.Status.ACTIVE)
            .select_related("plan")
            .order_by("-created_at")
            .first()
        )
        if not subscription:
            return Response(None)
        return Response(SubscriptionSerializer(subscription).data)


class SubscribeView(APIView):
    """POST /api/v1/subscriptions/subscribe/ {plan_id} — pricing-plans.tsx's
    "Choose Plan" button. Runs the (currently stubbed) payment provider,
    then deactivates any prior active subscription and activates the new
    one. Real payment failure handling (declined cards, retries, webhooks)
    belongs in the provider implementation once one exists — this view
    only needs to react to `ChargeResult.success`.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SubscribeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = get_object_or_404(SubscriptionPlan, pk=serializer.validated_data["plan_id"])

        result = get_payment_provider().charge(user=request.user, plan=plan)
        if not result.success:
            return Response({"detail": result.message}, status=402)

        Subscription.objects.filter(user=request.user, status=Subscription.Status.ACTIVE).update(
            status=Subscription.Status.EXPIRED
        )
        subscription = Subscription.objects.create(
            user=request.user,
            plan=plan,
            status=Subscription.Status.ACTIVE,
            payment_provider=result.provider,
            external_reference=result.external_reference,
        )
        return Response(SubscriptionSerializer(subscription).data, status=201)


class CancelSubscriptionView(APIView):
    """POST /api/v1/subscriptions/cancel/ — downgrades back to no active
    plan (the frontend treats "no active subscription" as the Free tier)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        subscription = get_object_or_404(
            Subscription, user=request.user, status=Subscription.Status.ACTIVE
        )
        get_payment_provider().cancel(subscription=subscription)
        subscription.status = Subscription.Status.CANCELLED
        subscription.cancelled_at = timezone.now()
        subscription.save(update_fields=["status", "cancelled_at", "updated_at"])
        return Response(SubscriptionSerializer(subscription).data)
