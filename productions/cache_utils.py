from django.conf import settings
from django.core.cache import cache


def bump_dashboard_cache_version() -> int:
    """
    Увеличивает версию кэша dashboard.

    Идея:
    - dashboard кэшируется не напрямую "навсегда", а через версионированный ключ;
    - при изменении данных мы просто увеличиваем номер версии;
    - старые ключи автоматически перестают использоваться.

    Это удобнее, чем вручную искать и удалять все связанные cache keys.
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
        # Если кэш временно не работает, не ломаем приложение.
        # Просто возвращаем безопасное значение.
        return 1
