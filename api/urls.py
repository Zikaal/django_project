from django.urls import path

from .views import ApiHealthView, ApiMeView, DailyProductionCreateApiView

urlpatterns = [
    path("health/", ApiHealthView.as_view(), name="api_health"),
    path("me/", ApiMeView.as_view(), name="api_me"),
    path("reports/daily/", DailyProductionCreateApiView.as_view(), name="api_dailyproduction_create"),
]