from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from .models import OilCompany

class OilCompanyListView(LoginRequiredMixin, ListView):
    model = OilCompany
    template_name = "companies/company_list.html"
    context_object_name = "companies"

    def get_queryset(self):
        return OilCompany.objects.prefetch_related("employees__user", "wells").order_by("name")