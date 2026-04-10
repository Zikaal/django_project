from django.conf import settings
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from accounts.models import Profile
from companies.models import OilCompany
from .models import DailyProduction, Well


def _bump_cache_version(key_name: str):
    try:
        current_value = cache.get(key_name)
        if current_value is None:
            cache.set(key_name, 1, None)
        else:
            cache.incr(key_name)
    except ValueError:
        cache.set(key_name, 2, None)
    except Exception:
        pass


def bump_dashboard_cache_version():
    _bump_cache_version(settings.DASHBOARD_CACHE_VERSION_KEY)


def bump_export_cache_version():
    _bump_cache_version(settings.EXPORT_CACHE_VERSION_KEY)


@receiver(post_save, sender=DailyProduction)
@receiver(post_delete, sender=DailyProduction)
@receiver(post_save, sender=Well)
@receiver(post_delete, sender=Well)
@receiver(post_save, sender=OilCompany)
@receiver(post_delete, sender=OilCompany)
@receiver(post_save, sender=Profile)
@receiver(post_delete, sender=Profile)
def invalidate_analytics_caches(*args, **kwargs):
    bump_dashboard_cache_version()
    bump_export_cache_version()