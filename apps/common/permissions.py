"""Shared DRF permission classes.

Role checks assume `request.user.role` is one of the `User.Role` choices
defined in `apps.accounts.models` — see that module for the source of
truth. Keeping every permission class here (instead of scattered per-app)
means a reviewer only has to look in one place to see the full authorization
model of the API.
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Object-level: only the object's `owner` (or `user`) may write to it.

    Works for any model exposing either an `owner` or a `user` FK to
    `settings.AUTH_USER_MODEL`, which covers Property, Review, Message, etc.
    """

    owner_fields = ("owner", "user")

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        for field in self.owner_fields:
            if hasattr(obj, field):
                return getattr(obj, field) == request.user
        return False


class IsLandlord(permissions.BasePermission):
    """Only landlord (or dual-role) accounts may access the view."""

    message = "This action is only available to landlord accounts."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("landlord", "both")
        )


class IsSearcher(permissions.BasePermission):
    """Only searcher/tenant (or dual-role) accounts may access the view."""

    message = "This action is only available to apartment-seeker accounts."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("searcher", "both")
        )


class IsAdminRole(permissions.BasePermission):
    """Staff/admin only — used for moderation endpoints (approve/reject listings)."""

    message = "This action requires administrator privileges."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class ReadOnly(permissions.BasePermission):
    """Allows only safe (GET/HEAD/OPTIONS) methods — used to compose e.g.
    `[IsAuthenticated | ReadOnly]` where anonymous browsing is fine but
    mutation requires auth."""

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS
