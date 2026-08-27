from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User, VerificationDocument


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ["email", "username", "role", "is_email_verified", "verification_status", "is_staff", "date_joined"]
    list_filter = ["role", "verification_status", "is_email_verified", "is_staff", "is_active"]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering = ["-date_joined"]
    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "Masskan profile",
            {
                "fields": (
                    "role",
                    "phone",
                    "avatar",
                    "bio",
                    "company_name",
                    "response_time_minutes",
                    "is_email_verified",
                    "verification_status",
                )
            },
        ),
    )


@admin.register(VerificationDocument)
class VerificationDocumentAdmin(admin.ModelAdmin):
    list_display = ["user", "doc_type", "status", "created_at", "reviewed_at"]
    list_filter = ["doc_type", "status"]
    search_fields = ["user__email"]
    autocomplete_fields = ["user", "reviewed_by"]
