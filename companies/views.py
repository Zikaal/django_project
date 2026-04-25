from django.db.models import Prefetch
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from accounts.mixins import AdminOrManagerScopedMixin, AdminRequiredMixin
from accounts.models import Profile
from accounts.utils import is_admin
from productions.models import Well

from .models import OilCompany


class OilCompanyListView(AdminOrManagerScopedMixin, ListView):
    """
    Список нефтяных компаний.

    Доступ:
    - Admin видит все компании;
    - Manager видит только свою компанию благодаря AdminOrManagerScopedMixin.

    Дополнительно:
    - поддерживает фильтрацию по региону;
    - поддерживает сортировку;
    - заранее подгружает связанные скважины и сотрудников.
    """

    model = OilCompany
    template_name = "companies/company_list.html"
    context_object_name = "companies"
    paginate_by = 20

    # Важно:
    # CompanyScopedMixin по умолчанию фильтрует по oil_company_id,
    # но здесь сама модель — это OilCompany.
    # Поэтому ограничение для Manager должно идти по полю id компании.
    company_filter_field = "id"

    def get_queryset(self):
        """
        Формирует queryset списка компаний.

        Оптимизации:
        - prefetch_related для wells и employees уменьшает количество SQL-запросов;
        - для employees дополнительно используем select_related("user", "oil_company"),
          чтобы сразу подтянуть связанные объекты профиля.
        """
        queryset = (
            super()
            .get_queryset()
            .prefetch_related(
                Prefetch("wells", queryset=Well.objects.order_by("name")),
                Prefetch(
                    "employees",
                    queryset=Profile.objects.select_related("user", "oil_company"),
                ),
            )
        )

        # Фильтр по региону.
        region = self.request.GET.get("region", "")

        # Параметр сортировки.
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
        """
        Добавляет в шаблон дополнительные данные:
        - текущую сортировку;
        - текущий фильтр по региону;
        - общее число компаний после фильтрации;
        - флаг is_admin для UI-логики;
        - query_string для пагинации с сохранением фильтров.
        """
        context = super().get_context_data(**kwargs)
        context["sort"] = self.request.GET.get("sort", "name")
        context["region"] = self.request.GET.get("region", "")
        context["total_count"] = self.get_queryset().count()
        context["is_admin"] = is_admin(self.request.user)

        # Убираем page, чтобы пагинация не ломала текущие фильтры.
        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["query_string"] = query_params.urlencode()

        return context


class OilCompanyCreateView(AdminRequiredMixin, CreateView):
    """
    Создание компании.

    Доступ:
    - только Admin.
    """

    model = OilCompany
    fields = ["name", "region"]
    template_name = "companies/company_form.html"
    success_url = reverse_lazy("company_list")


class OilCompanyUpdateView(AdminRequiredMixin, UpdateView):
    """
    Редактирование компании.

    Доступ:
    - только Admin.
    """

    model = OilCompany
    fields = ["name", "region"]
    template_name = "companies/company_form.html"
    success_url = reverse_lazy("company_list")


class OilCompanyDeleteView(AdminRequiredMixin, DeleteView):
    """
    Удаление компании.

    Доступ:
    - только Admin.
    """

    model = OilCompany
    template_name = "companies/company_confirm_delete.html"
    success_url = reverse_lazy("company_list")
