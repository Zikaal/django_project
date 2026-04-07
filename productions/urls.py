from django.urls import path

from .views import (
    DailyProductionCreateView,
    DailyProductionDeleteView,
    DailyProductionListView,
    DailyProductionUpdateView,
    DashboardView,
    WellCreateView,
    WellDeleteView,
    WellListView,
    WellUpdateView,
    DailyProductionImportView,
    MonthlyProductionExportView
)

urlpatterns = [
    # Dashboard
    path(
        "dashboard/",
        DashboardView.as_view(),
        name="dashboard",
    ),
    # ===================================================================
    # Маршруты для суточных рапортов по добыче (DailyProduction)
    # ===================================================================
    # Основной список рапортов (главная страница приложения productions)
    path(
        "",
        DailyProductionListView.as_view(),
        name="dailyproduction_list",
    ),
    # Создание нового суточного рапорта
    path(
        "create/",
        DailyProductionCreateView.as_view(),
        name="dailyproduction_create",
    ),
    # Редактирование существующего рапорта
    path(
        "<int:pk>/edit/",
        DailyProductionUpdateView.as_view(),
        name="dailyproduction_update",
    ),
    # Удаление рапорта
    path(
        "<int:pk>/delete/",
        DailyProductionDeleteView.as_view(),
        name="dailyproduction_delete",
    ),
    path(
        "import/",
        DailyProductionImportView.as_view(),
        name="dailyproduction_import",
        ),
    path(
        "export/monthly/",
        MonthlyProductionExportView.as_view(),
        name="dailyproduction_export",
        ),
    # ===================================================================
    # Маршруты для управления скважинами (Well)
    # ===================================================================
    # Список всех скважин с возможностью фильтрации и сортировки
    path(
        "wells/",
        WellListView.as_view(),
        name="well_list",
    ),
    # Создание новой скважины
    path(
        "wells/create/",
        WellCreateView.as_view(),
        name="well_create",
    ),
    # Редактирование скважины
    path(
        "wells/<int:pk>/edit/",
        WellUpdateView.as_view(),
        name="well_update",
    ),
    # Удаление скважины
    path(
        "wells/<int:pk>/delete/",
        WellDeleteView.as_view(),
        name="well_delete",
    ),
]
