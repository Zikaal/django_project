from django.urls import path

from .views import OilCompanyListView

urlpatterns = [
    path("", OilCompanyListView.as_view(), name="company_list"),
]