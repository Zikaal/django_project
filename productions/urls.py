from django.urls import path

from .views import (
    DailyProductionCreateView,
    DailyProductionDeleteView,
    DailyProductionImportView,
    DailyProductionListView,
    DailyProductionUpdateView,
    DashboardView,
    MonthlyProductionExportDownloadView,
    MonthlyProductionExportView,
    WellCreateView,
    WellDeleteView,
    WellListView,
    WellUpdateView,
)

# Маршруты приложения productions.
urlpatterns = [
    # Dashboard аналитики.
    path("dashboard/", DashboardView.as_view(), name="dashboard"),

    # Список суточных рапортов.
    path("", DailyProductionListView.as_view(), name="dailyproduction_list"),

    # CRUD для DailyProduction.
    path("create/", DailyProductionCreateView.as_view(), name="dailyproduction_create"),
    path("<int:pk>/edit/", DailyProductionUpdateView.as_view(), name="dailyproduction_update"),
    path("<int:pk>/delete/", DailyProductionDeleteView.as_view(), name="dailyproduction_delete"),

    # Импорт и экспорт.
    path("import/", DailyProductionImportView.as_view(), name="dailyproduction_import"),
    path("export/monthly/", MonthlyProductionExportView.as_view(), name="dailyproduction_export"),
    path(
        "export/monthly/<int:pk>/download/",
        MonthlyProductionExportDownloadView.as_view(),
        name="dailyproduction_export_download",
    ),

    # CRUD для Well.
    path("wells/", WellListView.as_view(), name="well_list"),
    path("wells/create/", WellCreateView.as_view(), name="well_create"),
    path("wells/<int:pk>/edit/", WellUpdateView.as_view(), name="well_update"),
    path("wells/<int:pk>/delete/", WellDeleteView.as_view(), name="well_delete"),
]