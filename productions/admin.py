from django.contrib import admin

from .models import DailyProduction, DailyProductionImportJob, Well


@admin.register(Well)
class WellAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "oil_company", "type", "max_drilling_depth", "latitude", "longitude")
    search_fields = ("name", "oil_company__name", "type")
    list_filter = ("oil_company", "type")
    ordering = ("name",)


@admin.register(DailyProduction)
class DailyProductionAdmin(admin.ModelAdmin):
    list_display = ("id", "well", "date", "work_time", "liquid_debit", "water_cut", "oil_density", "calculated_oil")
    search_fields = ("well__name", "well__oil_company__name")
    list_filter = ("date", "well__oil_company", "well")
    ordering = ("-date", "well__name")


@admin.register(DailyProductionImportJob)
class DailyProductionImportJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "uploaded_by",
        "status",
        "created_count",
        "skipped_count",
        "error_count",
        "uploaded_at",
        "started_at",
        "finished_at",
    )
    list_filter = ("status", "uploaded_at", "started_at", "finished_at")
    search_fields = ("uploaded_by__username", "uploaded_by__email", "celery_task_id")
    readonly_fields = (
        "status",
        "celery_task_id",
        "created_count",
        "skipped_count",
        "error_count",
        "errors_preview",
        "fatal_error",
        "uploaded_at",
        "started_at",
        "finished_at",
    )