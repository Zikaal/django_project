import os

from celery import Celery

# Указываем Django settings module по умолчанию.
# Это нужно, чтобы Celery знал, какие настройки Django использовать
# при запуске worker/process'ов.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Создаем экземпляр Celery-приложения.
# Имя "config" обычно совпадает с именем корневого Django-проекта.
app = Celery("config")

# Загружаем настройки Celery из Django settings.
#
# namespace="CELERY" означает, что Celery будет читать только те настройки,
# которые начинаются с префикса CELERY_.
#
# Например, в settings.py можно задавать:
# CELERY_BROKER_URL = "redis://localhost:6379/0"
# CELERY_RESULT_BACKEND = "redis://localhost:6379/1"
app.config_from_object("django.conf:settings", namespace="CELERY")

# Автоматически ищем tasks.py во всех установленных Django-приложениях.
#
# Это позволяет не импортировать задачи вручную.
# Если в приложении есть файл tasks.py, Celery его найдет и зарегистрирует задачи.
app.autodiscover_tasks()