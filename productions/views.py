from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

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