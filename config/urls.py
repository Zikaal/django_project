"""
Главная конфигурация URL-маршрутов проекта.

Этот файл является центральной точкой маршрутизации Django-приложения.
Здесь подключаются:
- админка;
- маршруты приложений accounts / productions / companies / notifications;
- DRF auth-маршруты;
- API v1;
- media-файлы в режиме DEBUG;
- Django Debug Toolbar в режиме DEBUG.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Административная панель Django.
    path("admin/", admin.site.urls),

    # Web-маршруты приложений проекта.
    path("accounts/", include("accounts.urls")),
    path("productions/", include("productions.urls")),
    path("companies/", include("companies.urls")),
    path("notifications/", include("notifications.urls")),

    # Встроенные маршруты Django REST Framework для браузерной авторизации.
    # Обычно используются в browsable API:
    # - login
    # - logout
    path("api-auth/", include("rest_framework.urls")),

    # API-маршруты версии v1.
    # auth_urls вынесены отдельно для логина/получения токена.
    path("api/v1/auth/", include("api.auth_urls")),
    path("api/v1/", include("api.urls")),
]

# Дополнительные маршруты, которые подключаются только в режиме разработки.
if settings.DEBUG:
    # Раздача media-файлов через Django dev-server.
    # В production это обычно делает nginx / object storage / CDN.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Подключение Django Debug Toolbar только в dev-режиме.
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns