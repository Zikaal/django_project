import json
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum, Value
from django.db.models.functions import Coalesce
from django.urls import reverse_lazy
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from accounts.models import Profile
from companies.models import OilCompany

from .forms import DailyProductionForm, WellForm
from .models import DailyProduction, Well


class WellListView(LoginRequiredMixin, ListView):
    """
    Представление для отображения списка скважин.

    Поддерживает:
    - Фильтрацию по нефтяной компании
    - Сортировку по названию скважины и компании
    - Пагинацию (20 записей на страницу)
    """

    model = Well
    template_name = "productions/well_list.html"
    context_object_name = "wells"
    paginate_by = 20

    def get_queryset(self):
        """
        Переопределяем queryset для:
        1. Оптимизации запросов через select_related
        2. Фильтрации по компании (GET-параметр "company")
        3. Сортировки по GET-параметру "sort"
        """
        queryset = Well.objects.select_related("oil_company")

        sort = self.request.GET.get("sort", "name")
        company_id = self.request.GET.get("company", "")

        # Фильтрация по выбранной компании
        if company_id:
            queryset = queryset.filter(oil_company_id=company_id)

        # Применяем сортировку
        if sort == "-name":
            queryset = queryset.order_by("-name")
        elif sort == "company":
            queryset = queryset.order_by("oil_company__name", "name")
        else:
            # Сортировка по умолчанию — по названию скважины
            queryset = queryset.order_by("name")

        return queryset

    def get_context_data(self, **kwargs):
        """
        Добавляем в контекст шаблона данные для фильтров и пагинации:
        - Список всех компаний для выпадающего списка
        - Текущие значения фильтров и сортировки
        - Общее количество скважин после фильтрации
        - Строку GET-параметров без "page"
        """
        context = super().get_context_data(**kwargs)

        context["companies"] = OilCompany.objects.order_by("name")
        context["selected_company"] = self.request.GET.get("company", "")
        context["sort"] = self.request.GET.get("sort", "name")
        context["total_count"] = self.get_queryset().count()

        # Сохраняем GET-параметры для корректной работы пагинации при фильтрации
        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["query_string"] = query_params.urlencode()

        return context


class WellCreateView(LoginRequiredMixin, CreateView):
    """
    Представление для создания новой скважины.
    Использует форму WellForm.
    После успешного создания перенаправляет на список скважин.
    """

    model = Well
    form_class = WellForm
    template_name = "productions/well_form.html"
    success_url = reverse_lazy("well_list")


class WellUpdateView(LoginRequiredMixin, UpdateView):
    """
    Представление для редактирования существующей скважины.
    Использует ту же форму и шаблон, что и создание.
    После успешного обновления перенаправляет на список скважин.
    """

    model = Well
    form_class = WellForm
    template_name = "productions/well_form.html"
    success_url = reverse_lazy("well_list")


class WellDeleteView(LoginRequiredMixin, DeleteView):
    """
    Представление для подтверждения и удаления скважины.
    Использует отдельный шаблон подтверждения удаления.
    После удаления перенаправляет на список скважин.
    """

    model = Well
    template_name = "productions/well_confirm_delete.html"
    success_url = reverse_lazy("well_list")


# ===========================================================================
# Ниже идут представления для DailyProduction
# ===========================================================================


class DailyProductionListView(LoginRequiredMixin, ListView):
    """
    Представление для отображения списка ежедневных отчётов по добыче нефти.

    Поддерживает:
    - Фильтрацию по нефтяной компании, скважине и диапазону дат
    - Сортировку по дате, скважине и компании
    - Пагинацию (по 20 записей на страницу)
    - Передачу параметров фильтров и сортировки в шаблон
    """

    model = DailyProduction
    template_name = "productions/dailyproduction_list.html"
    context_object_name = "reports"
    paginate_by = 20

    def get_queryset(self):
        """
        Переопределяем стандартный queryset для оптимизации, фильтрации и сортировки.
        """
        queryset = DailyProduction.objects.select_related("well", "well__oil_company")

        sort = self.request.GET.get("sort", "-date")
        company_id = self.request.GET.get("company")
        well_id = self.request.GET.get("well")
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")

        if company_id:
            queryset = queryset.filter(well__oil_company_id=company_id)

        if well_id:
            queryset = queryset.filter(well_id=well_id)

        if date_from:
            queryset = queryset.filter(date__gte=date_from)

        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        if sort == "date":
            queryset = queryset.order_by("date")
        elif sort == "well":
            queryset = queryset.order_by("well__name")
        elif sort == "company":
            queryset = queryset.order_by("well__oil_company__name", "well__name")
        else:
            queryset = queryset.order_by("-date", "well__name")

        return queryset

    def get_context_data(self, **kwargs):
        """
        Добавляем в контекст данные для фильтров и пагинации.
        """
        context = super().get_context_data(**kwargs)

        context["companies"] = OilCompany.objects.order_by("name")
        context["wells"] = Well.objects.select_related("oil_company").order_by("name")

        context["sort"] = self.request.GET.get("sort", "-date")
        context["selected_company"] = self.request.GET.get("company", "")
        context["selected_well"] = self.request.GET.get("well", "")
        context["date_from"] = self.request.GET.get("date_from", "")
        context["date_to"] = self.request.GET.get("date_to", "")

        context["total_count"] = self.get_queryset().count()

        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["query_string"] = query_params.urlencode()

        return context


class DailyProductionCreateView(LoginRequiredMixin, CreateView):
    """Представление для создания нового суточного рапорта по добыче."""

    model = DailyProduction
    form_class = DailyProductionForm
    template_name = "productions/dailyproduction_form.html"
    success_url = reverse_lazy("dailyproduction_list")


class DailyProductionUpdateView(LoginRequiredMixin, UpdateView):
    """Представление для редактирования суточного рапорта по добыче."""

    model = DailyProduction
    form_class = DailyProductionForm
    template_name = "productions/dailyproduction_form.html"
    success_url = reverse_lazy("dailyproduction_list")


class DailyProductionDeleteView(LoginRequiredMixin, DeleteView):
    """Представление для удаления суточного рапорта по добыче."""

    model = DailyProduction
    template_name = "productions/dailyproduction_confirm_delete.html"
    success_url = reverse_lazy("dailyproduction_list")


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "productions/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        company_ids = self.request.GET.getlist("company")
        company_ids = [company_id for company_id in company_ids if company_id]

        date_from = self.request.GET.get("date_from", "")
        date_to = self.request.GET.get("date_to", "")

        oil_formula = ExpressionWrapper(
            F("liquid_debit") * (Value(Decimal("1.0")) - F("water_cut") / Value(Decimal("100.0"))) * F("oil_density"),
            output_field=DecimalField(max_digits=14, decimal_places=4),
        )

        reports_qs = DailyProduction.objects.select_related("well", "well__oil_company")
        wells_qs = Well.objects.select_related("oil_company")
        profiles_qs = Profile.objects.select_related("oil_company")
        companies_qs = OilCompany.objects.all()

        if company_ids:
            reports_qs = reports_qs.filter(well__oil_company_id__in=company_ids)
            wells_qs = wells_qs.filter(oil_company_id__in=company_ids)
            profiles_qs = profiles_qs.filter(oil_company_id__in=company_ids)
            companies_qs = companies_qs.filter(id__in=company_ids)

        if date_from:
            reports_qs = reports_qs.filter(date__gte=date_from)

        if date_to:
            reports_qs = reports_qs.filter(date__lte=date_to)

        context["companies"] = OilCompany.objects.order_by("name")
        context["selected_companies"] = company_ids
        context["date_from"] = date_from
        context["date_to"] = date_to

        context["total_companies"] = companies_qs.count()
        context["total_wells"] = wells_qs.count()
        context["total_users"] = profiles_qs.count()
        context["total_reports"] = reports_qs.count()

        production_by_date = (
            reports_qs.values("date")
            .annotate(
                total_oil=Coalesce(
                    Sum(oil_formula),
                    0,
                    output_field=DecimalField(max_digits=14, decimal_places=4),
                )
            )
            .order_by("date")
        )

        line_labels = [item["date"].strftime("%Y-%m-%d") for item in production_by_date]
        line_data = [float(item["total_oil"]) for item in production_by_date]

        production_by_well = (
            reports_qs.values("well__name")
            .annotate(
                total_oil=Coalesce(
                    Sum(oil_formula),
                    0,
                    output_field=DecimalField(max_digits=14, decimal_places=4),
                )
            )
            .order_by("-total_oil", "well__name")[:10]
        )

        bar_labels = [item["well__name"] for item in production_by_well]
        bar_data = [float(item["total_oil"]) for item in production_by_well]

        wells_by_company = (
            wells_qs.values("oil_company__name").annotate(wells_count=Count("id")).order_by("oil_company__name")
        )

        pie_labels = [item["oil_company__name"] for item in wells_by_company]
        pie_data = [item["wells_count"] for item in wells_by_company]

        users_by_company = (
            profiles_qs.values("oil_company__name").annotate(users_count=Count("id")).order_by("oil_company__name")
        )

        doughnut_labels = [item["oil_company__name"] for item in users_by_company]
        doughnut_data = [item["users_count"] for item in users_by_company]

        context["line_labels"] = json.dumps(line_labels, ensure_ascii=False)
        context["line_data"] = json.dumps(line_data)

        context["bar_labels"] = json.dumps(bar_labels, ensure_ascii=False)
        context["bar_data"] = json.dumps(bar_data)

        context["pie_labels"] = json.dumps(pie_labels, ensure_ascii=False)
        context["pie_data"] = json.dumps(pie_data)

        context["doughnut_labels"] = json.dumps(doughnut_labels, ensure_ascii=False)
        context["doughnut_data"] = json.dumps(doughnut_data)

        return context
