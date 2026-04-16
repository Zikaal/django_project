from django.apps import AppConfig


class ApiConfig(AppConfig):
    """
    Конфигурация Django-приложения api.

    Используется Django при загрузке приложения.
    Здесь можно:
    - подключать signals;
    - выполнять startup-инициализацию;
    - хранить базовые настройки app.
    """

    name = "api"