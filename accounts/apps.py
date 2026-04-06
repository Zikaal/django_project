from django.apps import AppConfig  # Импортируем базовый класс AppConfig для настройки приложения Django


class AccountsConfig(AppConfig):  # Создаем класс конфигурации для приложения accounts
    default_auto_field = "django.db.models.BigAutoField"  # Тип поля первичного ключа по умолчанию для моделей (если id не указан вручную, Django создаст BigAutoField)
    name = "accounts"  # Имя приложения Django

    def ready(self):  # Метод, который вызывается, когда приложение полностью загружено
        pass  # Импортируем файл signals, чтобы Django зарегистрировал обработчики сигналов
