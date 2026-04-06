from django.contrib import admin

from .models import DailyProduction, Well


@admin.register(Well)
class WellAdmin(admin.ModelAdmin):
    """Админка для скважин"""

    list_display = ("id", "name", "oil_company", "type", "max_drilling_depth", "latitude", "longitude")
    search_fields = ("name", "oil_company__name", "type")
    list_filter = ("oil_company", "type")
    ordering = ("name",)


@admin.register(DailyProduction)
class DailyProductionAdmin(admin.ModelAdmin):
    """Админка для суточной добычи"""

    list_display = ("id", "well", "date", "work_time", "liquid_debit", "water_cut", "oil_density", "calculated_oil")
    search_fields = ("well__name", "well__oil_company__name")
    list_filter = ("date", "well__oil_company", "well")
    ordering = ("-date", "well__name")
