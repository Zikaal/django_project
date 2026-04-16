from django.urls import path

from .views import MobileObtainAuthTokenView

# Отдельные auth-маршруты API.
# Сейчас здесь только endpoint получения токена.
urlpatterns = [
    path("token/", MobileObtainAuthTokenView.as_view(), name="api_token_auth"),
]