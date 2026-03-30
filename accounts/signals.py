from django.conf import settings  # Импортируем настройки проекта Django
from django.db.models.signals import post_save  # Импортируем сигнал post_save, который срабатывает после сохранения объекта
from django.dispatch import receiver  # Импортируем декоратор receiver для подключения функции к сигналу
from .models import Profile  # Импортируем модель Profile из текущего приложения
from companies.models import OilCompany

@receiver(post_save, sender=settings.AUTH_USER_MODEL)  # Подключаем функцию к сигналу post_save для модели пользователя
def create_user_profile(sender, instance, created, raw, **kwargs):  # Функция, которая будет вызываться после сохранения пользователя
    if raw:  # Проверяем, загружается ли объект "сырым" способом, например из fixture
        return  # Если да, выходим и не создаем профиль

    if created:
        company = OilCompany.objects.first()  # 👈 ВАЖНО

        Profile.objects.create(
            user=instance,
            oil_company=company  # 👈 теперь не будет NULL
        )