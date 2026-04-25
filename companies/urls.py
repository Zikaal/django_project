from django.urls import path

from .views import (
    OilCompanyCreateView,
    OilCompanyDeleteView,
    OilCompanyListView,
    OilCompanyUpdateView,
)

# URL-маршруты приложения companies.
# Отвечают за список, создание, редактирование и удаление компаний.
urlpatterns = [
    # Список нефтяных компаний.
    path(
        "",
        OilCompanyListView.as_view(),
        name="company_list",
    ),
    # Создание новой компании.
    path(
        "create/",
        OilCompanyCreateView.as_view(),
        name="company_create",
    ),
    # Редактирование существующей компании по pk.
    path(
        "<int:pk>/edit/",
        OilCompanyUpdateView.as_view(),
        name="company_update",
    ),
    # Удаление компании по pk.
    path(
        "<int:pk>/delete/",
        OilCompanyDeleteView.as_view(),
        name="company_delete",
    ),
]
