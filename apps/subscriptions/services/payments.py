"""Payment provider interface.

Per product decision, real payment collection (Stripe/Paymob/etc.) is out of
scope for this build — pricing-plans.tsx just needs a working "subscribe"
flow to call, and the project needs a clean seam to drop a real provider
into later without touching views/serializers.

`get_payment_provider()` is the ONLY place the rest of the app should reach
for a provider — swap the return value (or branch on
`settings.PAYMENTS_PROVIDER`) once a real integration exists.
"""

import abc
from dataclasses import dataclass


@dataclass
class ChargeResult:
    success: bool
    provider: str
    external_reference: str
    message: str = ""


class PaymentProvider(abc.ABC):
    """Minimal interface any real gateway integration (Stripe, Paymob, ...)
    would implement. Only what `SubscribeView` needs is modeled here —
    extend as real billing requirements (webhooks, refunds, invoices) show
    up.
    """

    name = "base"

    @abc.abstractmethod
    def charge(self, *, user, plan) -> ChargeResult:
        """Attempt to collect payment for `user` subscribing to `plan`."""

    @abc.abstractmethod
    def cancel(self, *, subscription) -> ChargeResult:
        """Attempt to cancel a subscription with the provider."""


class StubPaymentProvider(PaymentProvider):
    """Always succeeds without moving any money — lets the rest of the
    subscribe/cancel flow (plan limits, DB state, response shape) be built
    and tested end-to-end today. Replace with a real provider by adding a
    class here (e.g. `StripePaymentProvider`) and switching it in
    `get_payment_provider()`; no other code needs to change.
    """

    name = "stub"

    def charge(self, *, user, plan) -> ChargeResult:
        return ChargeResult(
            success=True,
            provider=self.name,
            external_reference=f"stub_charge_{user.pk}_{plan.pk}",
            message="Simulated charge — no real payment provider is configured yet.",
        )

    def cancel(self, *, subscription) -> ChargeResult:
        return ChargeResult(
            success=True,
            provider=self.name,
            external_reference=subscription.external_reference or "",
            message="Simulated cancellation — no real payment provider is configured yet.",
        )


def get_payment_provider() -> PaymentProvider:
    # Only "stub" exists today; this indirection is the whole point — a
    # future `PAYMENTS_PROVIDER=stripe` in settings would branch here.
    return StubPaymentProvider()
