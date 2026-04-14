from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from accounts.models import Profile
from productions.models import Well
from accounts.mixins import AdminOrManagerScopedMixin, AdminRequiredMixin
from accounts.utils import get_user_company, is_admin
from .models import OilCompany
from django.db.models import Prefetch

class OilCompanyListView(AdminOrManagerScopedMixin, ListView):
    model = OilCompany
    template_name = "companies/company_list.html"
    context_object_name = "companies"
    paginate_by = 20
    company_filter_field = "id"

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .prefetch_related(
                Prefetch("wells", queryset=Well.objects.order_by("name")),
                Prefetch(
                    "employees",
                    queryset=Profile.objects.select_related("user", "oil_company")
                ),
            )
        )

        region = self.request.GET.get("region", "")
        sort = self.request.GET.get("sort", "name")

        if region:
            queryset = queryset.filter(region__icontains=region)

        if sort == "-name":
            queryset = queryset.order_by("-name")
        elif sort == "region":
            queryset = queryset.order_by("region", "name")
        else:
            queryset = queryset.order_by("name")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sort"] = self.request.GET.get("sort", "name")
        context["region"] = self.request.GET.get("region", "")
        context["total_count"] = self.get_queryset().count()
        context["is_admin"] = is_admin(self.request.user)

        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["query_string"] = query_params.urlencode()

        return context


class OilCompanyCreateView(AdminRequiredMixin, CreateView):
    """Создание компании — только Admin."""
    model = OilCompany
    fields = ["name", "region"]
    template_name = "companies/company_form.html"
    success_url = reverse_lazy("company_list")


class OilCompanyUpdateView(AdminRequiredMixin, UpdateView):
    """Редактирование компании — только Admin."""
    model = OilCompany
    fields = ["name", "region"]
    template_name = "companies/company_form.html"
    success_url = reverse_lazy("company_list")


class OilCompanyDeleteView(AdminRequiredMixin, DeleteView):
    """Удаление компании — только Admin."""
    model = OilCompany
    template_name = "companies/company_confirm_delete.html"
    success_url = reverse_lazy("company_list")