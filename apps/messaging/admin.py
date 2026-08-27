from django.contrib import admin

from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ["sender", "text", "is_read", "created_at"]
    readonly_fields = ["created_at"]
    autocomplete_fields = ["sender"]


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "property", "initiator", "recipient", "updated_at"]
    list_filter = ["created_at"]
    autocomplete_fields = ["property", "initiator", "recipient"]
    search_fields = ["initiator__email", "recipient__email", "property__title"]
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["id", "conversation", "sender", "is_read", "created_at"]
    list_filter = ["is_read"]
    autocomplete_fields = ["conversation", "sender"]
    search_fields = ["text", "sender__email"]
