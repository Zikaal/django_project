from django.apps import AppConfig


class ProductionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "productions"

    def ready(self):
        import productions.signals  # noqa: F401