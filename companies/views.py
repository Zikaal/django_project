from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .models import OilCompany


class OilCompanyListView(LoginRequiredMixin, ListView):
    """
    Представление для отображения списка нефтяных компаний.

    Поддерживает:
    - Фильтрацию по региону (поиск по подстроке)
    - Пагинацию (20 записей на странице)
    - Сортировку по названию компании и региону
    - Оптимизацию запросов через prefetch_related
    - Передачу параметров фильтрации и сортировки в шаблон
    """

    model = OilCompany
    template_name = "companies/company_list.html"
    context_object_name = "companies"  # имя переменной в шаблоне
    paginate_by = 20  # количество компаний на одной странице

    def get_queryset(self):
        """
        Переопределяем queryset для:
        1. Оптимизации загрузки связанных данных (сотрудники и скважины)
        2. Фильтрации по региону (GET-параметр "region")
        3. Применения сортировки по GET-параметру "sort"
        """
        sort = self.request.GET.get("sort", "name")
        region = self.request.GET.get("region", "")

        # prefetch_related для оптимизации: загружаем связанные объекты заранее
        # "employees__user" — загружает пользователей через связь Employee → User
        # "wells" — загружает все скважины компаний
        queryset = OilCompany.objects.prefetch_related(
            "employees__user",
            "wells",
        )

        # Фильтрация по региону (регистронезависимый поиск по подстроке)
        if region:
            queryset = queryset.filter(region__icontains=region)

        # Применяем сортировку
        if sort == "region":
            queryset = queryset.order_by("region", "name")
        elif sort == "-name":
            queryset = queryset.order_by("-name")
        else:
            # Сортировка по умолчанию — по названию компании
            queryset = queryset.order_by("name")

        return queryset

    def get_context_data(self, **kwargs):
        """
        Добавляем в контекст шаблона дополнительные данные:
        - Текущий выбранный тип сортировки
        - Текущий фильтр по региону (для сохранения состояния формы)
        - Общее количество компаний в базе
        - Строку GET-параметров без 'page' (для корректной работы пагинации)
        """
        context = super().get_context_data(**kwargs)

        context["sort"] = self.request.GET.get("sort", "name")
        context["region"] = self.request.GET.get("region", "")

        # Общее количество компаний (используется для отображения статистики)
        context["total_count"] = OilCompany.objects.count()

        # Сохраняем все GET-параметры кроме 'page'
        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["query_string"] = query_params.urlencode()

        return context


class OilCompanyCreateView(LoginRequiredMixin, CreateView):
    """
    Представление для создания новой нефтяной компании.
    Использует встроенные поля модели (fields) без отдельной формы.
    После успешного создания перенаправляет на список компаний.
    """

    model = OilCompany
    fields = ["name", "region"]
    template_name = "companies/company_form.html"
    success_url = reverse_lazy("company_list")


class OilCompanyUpdateView(LoginRequiredMixin, UpdateView):
    """
    Представление для редактирования нефтяной компании.
    Использует те же поля и шаблон, что и создание.
    После успешного обновления перенаправляет на список компаний.
    """

    model = OilCompany
    fields = ["name", "region"]
    template_name = "companies/company_form.html"
    success_url = reverse_lazy("company_list")


class OilCompanyDeleteView(LoginRequiredMixin, DeleteView):
    """
    Представление для подтверждения и удаления нефтяной компании.
    Использует отдельный шаблон подтверждения удаления.
    После удаления перенаправляет на список компаний.
    """

    model = OilCompany
    template_name = "companies/company_confirm_delete.html"
    success_url = reverse_lazy("company_list")
