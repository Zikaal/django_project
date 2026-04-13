from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from accounts.mixins import AdminOrManagerMixin, AdminRequiredMixin
from accounts.utils import get_user_company, is_admin
from .models import OilCompany


class OilCompanyListView(AdminOrManagerMixin, ListView):
    """
    Список нефтяных компаний.

    Admin — видит все компании, может фильтровать по региону.
    Manager — видит только свою компанию.
    Operator — доступа нет (403).
    """

    model = OilCompany
    template_name = "companies/company_list.html"
    context_object_name = "companies"
    paginate_by = 20

    def get_queryset(self):
        sort = self.request.GET.get("sort", "name")
        region = self.request.GET.get("region", "")

        queryset = OilCompany.objects.prefetch_related("employees__user", "wells")

        if not is_admin(self.request.user):
            # Manager видит только свою компанию
            user_company = get_user_company(self.request.user)
            queryset = queryset.filter(id=user_company.id) if user_company else queryset.none()
        else:
            if region:
                queryset = queryset.filter(region__icontains=region)

        if sort == "region":
            queryset = queryset.order_by("region", "name")
        elif sort == "-name":
            queryset = queryset.order_by("-name")
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