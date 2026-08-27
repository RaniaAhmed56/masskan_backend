from django.contrib import admin

from .models import VisitRequest


@admin.register(VisitRequest)
class VisitRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "property", "requester", "visit_date", "visit_time", "status"]
    list_filter = ["status", "visit_date"]
    autocomplete_fields = ["property", "requester"]
    search_fields = ["full_name", "email", "phone", "property__title"]
