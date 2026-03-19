from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from .forms import DailyProductionForm
from .models import DailyProduction

class DailyProductionListView(LoginRequiredMixin, ListView):  # Создаем view для отображения списка суточных рапортов, доступное только авторизованным пользователям
    model = DailyProduction  # Указываем модель, объекты которой будут выводиться в списке
    template_name = "productions/dailyproduction_list.html"  # Указываем HTML-шаблон страницы со списком рапортов
    context_object_name = "reports"  # Задаем имя переменной, через которую список будет доступен в шаблоне

    def get_queryset(self):  # Переопределяем метод получения набора объектов для списка
        return DailyProduction.objects.select_related("well").order_by("-date", "well__name")  # Получаем все рапорты вместе со связанными скважинами и сортируем сначала по убыванию даты, затем по имени скважины


class DailyProductionCreateView(LoginRequiredMixin, CreateView):  # Создаем view для добавления нового суточного рапорта, доступное только авторизованным пользователям
    model = DailyProduction  # Указываем модель, объект которой будет создаваться
    form_class = DailyProductionForm  # Указываем форму, которая будет использоваться для создания записи
    template_name = "productions/dailyproduction_form.html"  # Указываем HTML-шаблон формы создания
    success_url = reverse_lazy("dailyproduction_list")  # После успешного создания перенаправляем пользователя на страницу списка рапортов


class DailyProductionUpdateView(LoginRequiredMixin, UpdateView):  # Создаем view для редактирования существующего суточного рапорта, доступное только авторизованным пользователям
    model = DailyProduction  # Указываем модель, объект которой будет редактироваться
    form_class = DailyProductionForm  # Указываем форму, которая будет использоваться для редактирования записи
    template_name = "productions/dailyproduction_form.html"  # Указываем HTML-шаблон формы редактирования
    success_url = reverse_lazy("dailyproduction_list")  # После успешного сохранения перенаправляем пользователя на страницу списка рапортов


class DailyProductionDeleteView(LoginRequiredMixin, DeleteView):  # Создаем view для удаления суточного рапорта, доступное только авторизованным пользователям
    model = DailyProduction  # Указываем модель, объект которой будет удаляться
    template_name = "productions/dailyproduction_confirm_delete.html"  # Указываем HTML-шаблон страницы подтверждения удаления
    success_url = reverse_lazy("dailyproduction_list")  # После успешного удаления перенаправляем пользователя на страницу списка рапортов