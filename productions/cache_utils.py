from django.conf import settings
from django.core.cache import cache


def bump_dashboard_cache_version() -> int:
    """
    Увеличивает версию кэша dashboard.
    Старые ключи становятся неактуальными автоматически.
    """
    key = settings.DASHBOARD_CACHE_VERSION_KEY

    try:
        current = cache.get(key)
        if current is None:
            current = 1

        new_version = int(current) + 1
        cache.set(key, new_version, None)
        return new_version
    except Exception:
        # Если cache временно недоступен, не ломаем приложение
        return 1