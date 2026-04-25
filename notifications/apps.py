from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """
    Конфигурация Django-приложения notifications.

    Django использует этот класс при загрузке приложения.
    Здесь можно:
    - подключать signals;
    - выполнять startup-инициализацию;
    - хранить базовые настройки приложения.
    """

    # Тип primary key по умолчанию для новых моделей приложения.
    default_auto_field = "django.db.models.BigAutoField"

    # Внутреннее имя приложения Django.
    name = "notifications"
