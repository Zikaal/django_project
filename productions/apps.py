from django.apps import AppConfig


class ProductionsConfig(AppConfig):
    """
    Конфигурация Django-приложения productions.

    Зачем нужен ready():
    - при старте приложения импортирует signals.py;
    - это регистрирует signal-handler'ы для аудита и инвалидации кэша.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "productions"

    def ready(self):
        # Импорт нужен не для прямого использования,
        # а для регистрации сигналов через декораторы @receiver.
        import productions.signals  # noqa: F401