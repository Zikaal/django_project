from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Настройка административной панели для модели Profile."""

    list_display = ("id", "user", "oil_company", "department", "phone_number")
    search_fields = ("user__username", "department", "phone_number", "oil_company__name")
    list_filter = ("oil_company", "department")
    ordering = ("user__username",)