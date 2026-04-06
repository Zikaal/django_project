from django.contrib import admin

from .models import OilCompany


@admin.register(OilCompany)
class OilCompanyAdmin(admin.ModelAdmin):
    """Админка для модели OilCompany."""

    list_display = ("id", "name", "region")
    search_fields = ("name", "region")
    list_filter = ("region",)
    ordering = ("name",)
