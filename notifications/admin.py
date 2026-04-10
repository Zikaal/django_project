from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "recipient",
        "title",
        "level",
        "is_read",
        "created_at",
        "read_at",
    )
    list_filter = ("level", "is_read", "created_at")
    search_fields = ("recipient__username", "recipient__email", "title", "message")
    readonly_fields = ("created_at", "read_at")