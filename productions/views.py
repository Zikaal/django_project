from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from companies.models import OilCompany
from .forms import DailyProductionForm
from .models import DailyProduction, Well


class DailyProductionListView(LoginRequiredMixin, ListView):
    """
    Представление для отображения списка ежедневных отчётов по добыче нефти.

    Поддерживает:
    - Фильтрацию по нефтяной компании, скважине и диапазону дат
    - Сортировку по дате, скважине и компании
    - Пагинацию (по 20 записей на страницу)
    - Передачу параметров фильтров и сортировки в шаблон для построения формы фильтров
    """

    model = DailyProduction
    template_name = "productions/dailyproduction_list.html"
    context_object_name = "reports"   # имя переменной в шаблоне
    paginate_by = 20                  # количество записей на одной странице

    def get_queryset(self):
        """
        Переопределяем стандартный queryset для:
        1. Оптимизации запросов через select_related (уменьшение количества SQL-запросов)
        2. Применения фильтров из GET-параметров
        3. Применения сортировки
        """
        # Оптимизируем загрузку связанных объектов (well и oil_company)
        queryset = DailyProduction.objects.select_related("well", "well__oil_company")

        # Получаем параметры фильтрации и сортировки из URL
        sort = self.request.GET.get("sort", "-date")
        company_id = self.request.GET.get("company")
        well_id = self.request.GET.get("well")
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")

        # Фильтрация по компании
        if company_id:
            queryset = queryset.filter(well__oil_company_id=company_id)

        # Фильтрация по конкретной скважине
        if well_id:
            queryset = queryset.filter(well_id=well_id)

        # Фильтрация по дате "от"
        if date_from:
            queryset = queryset.filter(date__gte=date_from)

        # Фильтрация по дате "до"
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        # Применяем сортировку
        if sort == "date":
            queryset = queryset.order_by("date")
        elif sort == "well":
            queryset = queryset.order_by("well__name")
        elif sort == "company":
            queryset = queryset.order_by("well__oil_company__name", "well__name")
        else:
            # Сортировка по умолчанию: сначала новые записи, потом по названию скважины
            queryset = queryset.order_by("-date", "well__name")

        return queryset

    def get_context_data(self, **kwargs):
        """
        Добавляем в контекст шаблона дополнительные данные:
        - Список всех компаний и скважин для выпадающих списков фильтров
        - Текущие выбранные значения фильтров (для сохранения состояния формы)
        - Строку запроса без параметра page (для корректной работы пагинации с фильтрами)
        - Общее количество записей после фильтрации
        """
        context = super().get_context_data(**kwargs)

        # Списки для фильтров
        context["companies"] = OilCompany.objects.order_by("name")
        context["wells"] = Well.objects.select_related("oil_company").order_by("name")

        # Передаём текущие значения фильтров в шаблон
        context["sort"] = self.request.GET.get("sort", "-date")
        context["selected_company"] = self.request.GET.get("company", "")
        context["selected_well"] = self.request.GET.get("well", "")
        context["date_from"] = self.request.GET.get("date_from", "")
        context["date_to"] = self.request.GET.get("date_to", "")

        # Общее количество записей (после фильтрации)
        context["total_count"] = self.get_queryset().count()

        # Сохраняем все GET-параметры кроме 'page' для корректной пагинации
        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["query_string"] = query_params.urlencode()

        return context


class DailyProductionCreateView(LoginRequiredMixin, CreateView):
    """
    Представление для создания новой записи ежедневной добычи.
    Использует кастомную форму DailyProductionForm.
    После успешного создания перенаправляет на список отчётов.
    """

    model = DailyProduction
    form_class = DailyProductionForm
    template_name = "productions/dailyproduction_form.html"
    success_url = reverse_lazy("dailyproduction_list")


class DailyProductionUpdateView(LoginRequiredMixin, UpdateView):
    """
    Представление для редактирования существующей записи ежедневной добычи.
    Использует ту же форму и шаблон, что и создание.
    После успешного обновления перенаправляет на список отчётов.
    """

    model = DailyProduction
    form_class = DailyProductionForm
    template_name = "productions/dailyproduction_form.html"
    success_url = reverse_lazy("dailyproduction_list")


class DailyProductionDeleteView(LoginRequiredMixin, DeleteView):
    """
    Представление для подтверждения и удаления записи ежедневной добычи.
    Использует отдельный шаблон подтверждения удаления.
    После удаления перенаправляет на список отчётов.
    """

    model = DailyProduction
    template_name = "productions/dailyproduction_confirm_delete.html"
    success_url = reverse_lazy("dailyproduction_list")