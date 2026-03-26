from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from .models import OilCompany


class OilCompanyListView(LoginRequiredMixin, ListView):
    """
    Представление для отображения списка нефтяных компаний.

    Поддерживает:
    - Пагинацию (20 записей на странице)
    - Сортировку по названию компании и региону
    - Оптимизацию запросов через prefetch_related
    - Передачу параметров сортировки и пагинации в шаблон
    """

    model = OilCompany
    template_name = "companies/company_list.html"
    context_object_name = "companies"   # имя переменной в шаблоне
    paginate_by = 20                    # количество компаний на одной странице

    def get_queryset(self):
        """
        Переопределяем queryset для:
        1. Оптимизации загрузки связанных данных (сотрудники и скважины)
        2. Применения сортировки по GET-параметру 'sort'
        """
        sort = self.request.GET.get("sort", "name")

        # prefetch_related используется для оптимизации: загружаем связанные объекты заранее
        # "employees__user" — загружает пользователей через связь Employee → User
        # "wells" — загружает все скважины компаний
        queryset = OilCompany.objects.prefetch_related(
            "employees__user",
            "wells",
        )

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
        - Общее количество компаний (без учета пагинации)
        - Строку GET-параметров без 'page' (для сохранения фильтров при переходе по страницам)
        """
        context = super().get_context_data(**kwargs)

        context["sort"] = self.request.GET.get("sort", "name")
        
        # Общее количество компаний в базе (используется для отображения статистики)
        context["total_count"] = OilCompany.objects.count()

        # Сохраняем все GET-параметры кроме 'page' для корректной работы пагинации
        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["query_string"] = query_params.urlencode()

        return context