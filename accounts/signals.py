from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, raw, **kwargs):
    """Создаёт пустой профиль без привязки к фиктивной компании."""
    if raw or not created:
        return

    Profile.objects.get_or_create(
        user=instance,
        defaults={
            "oil_company": None,
            "department": "",
            "phone_number": "",
            "bio": "",
        },
    )