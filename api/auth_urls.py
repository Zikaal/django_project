from django.urls import path

from .views import MobileObtainAuthTokenView

urlpatterns = [
    path("token/", MobileObtainAuthTokenView.as_view(), name="api_token_auth"),
]