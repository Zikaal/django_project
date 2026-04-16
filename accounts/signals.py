from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, raw, **kwargs):
    """
    Signal-handler, который автоматически создает профиль для нового пользователя.

    Когда срабатывает:
    - после сохранения модели пользователя (post_save);
    - только для AUTH_USER_MODEL проекта.

    Параметры:
    - sender: модель-источник сигнала;
    - instance: конкретный пользователь, который был сохранен;
    - created: True, если пользователь создан впервые;
    - raw: True, если сохранение идет в "сыром" режиме
      (например, при загрузке fixture), где нежелательно выполнять обычную логику.

    Зачем нужен сигнал:
    - гарантирует, что у каждого пользователя будет связанный Profile;
    - упрощает остальной код, потому что меньше шансов столкнуться
      с ситуацией "пользователь есть, а профиля нет".

    Почему используем get_or_create:
    - даже если сигнал сработает повторно, дубликат профиля не создастся.
    """
    # Если данные загружаются "сыро" (raw=True), либо объект не новый,
    # профиль создавать не нужно.
    if raw or not created:
        return

    # Создаем профиль с безопасными значениями по умолчанию.
    # Компания ставится None, потому что не всех пользователей нужно
    # сразу привязывать к компании.
    Profile.objects.get_or_create(
        user=instance,
        defaults={
            "oil_company": None,
            "department": "",
            "phone_number": "",
            "bio": "",
        },
    )