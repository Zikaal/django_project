from django.urls import path

from .views import ApiHealthView, ApiMeView, DailyProductionCreateApiView

# Основные маршруты API.
# Здесь регистрируются:
# - служебный health-check,
# - endpoint текущего пользователя,
# - создание суточного рапорта.
urlpatterns = [
    # Проверка, что API-сервис доступен и работает.
    path("health/", ApiHealthView.as_view(), name="api_health"),

    # Возвращает данные текущего авторизованного пользователя.
    path("me/", ApiMeView.as_view(), name="api_me"),

    # Создание суточного производственного рапорта.
    path(
        "reports/daily/",
        DailyProductionCreateApiView.as_view(),
        name="api_dailyproduction_create",
    ),
]