from django.apps import AppConfig


class CompaniesConfig(AppConfig):
    """
    Конфигурация Django-приложения companies.

    Django использует этот класс при загрузке приложения.
    Здесь можно:
    - регистрировать signals;
    - задавать default_auto_field;
    - выполнять startup-инициализацию.
    """

    # Внутреннее имя приложения.
    name = "companies"