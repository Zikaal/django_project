from django.urls import path

from .views import (
    OilCompanyCreateView,
    OilCompanyDeleteView,
    OilCompanyListView,
    OilCompanyUpdateView,
)

urlpatterns = [
    # ===================================================================
    # Маршруты для нефтяных компаний (OilCompany)
    # ===================================================================
    # Список всех нефтяных компаний с поддержкой фильтрации и сортировки
    path(
        "",
        OilCompanyListView.as_view(),
        name="company_list",
    ),
    # Создание новой нефтяной компании
    path(
        "create/",
        OilCompanyCreateView.as_view(),
        name="company_create",
    ),
    # Редактирование существующей нефтяной компании
    path(
        "<int:pk>/edit/",
        OilCompanyUpdateView.as_view(),
        name="company_update",
    ),
    # Удаление нефтяной компании
    path(
        "<int:pk>/delete/",
        OilCompanyDeleteView.as_view(),
        name="company_delete",
    ),
]
