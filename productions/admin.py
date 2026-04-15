from django.contrib import admin

from .models import (
    DailyProduction,
    DailyProductionImportJob,
    ProductionAuditLog,
    Well,
)


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


@admin.register(ProductionAuditLog)
class ProductionAuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "changed_at",
        "action",
        "changed_by_username",
        "well_name_snapshot",
        "report_date_snapshot",
        "field_name",
        "old_value",
        "new_value",
    )
    list_filter = (
        "action",
        "changed_at",
        "field_name",
        "well",
        "changed_by",
    )
    search_fields = (
        "changed_by_username",
        "changed_by__username",
        "changed_by__email",
        "well_name_snapshot",
        "well__name",
        "field_name",
        "field_verbose_name",
        "message",
    )
    ordering = ("-changed_at",)
    readonly_fields = (
        "daily_production",
        "well",
        "changed_by",
        "changed_by_username",
        "well_name_snapshot",
        "report_date_snapshot",
        "action",
        "field_name",
        "field_verbose_name",
        "old_value",
        "new_value",
        "message",
        "changed_at",
    )

    list_select_related = ("daily_production", "well", "changed_by")
    date_hierarchy = "changed_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False