from django.urls import path

from .views import DailyProductionListView, DailyProductionCreateView, DailyProductionUpdateView, DailyProductionDeleteView

urlpatterns = [  # Список URL-маршрутов приложения productions
    path("", DailyProductionListView.as_view(), name="dailyproduction_list"),  # Главная страница раздела productions: отображает список всех суточных рапортов
    path("create/", DailyProductionCreateView.as_view(), name="dailyproduction_create"),  # Страница создания нового суточного рапорта
    path("<int:pk>/edit/", DailyProductionUpdateView.as_view(), name="dailyproduction_update"),  # Страница редактирования рапорта по его id
    path("<int:pk>/delete/", DailyProductionDeleteView.as_view(), name="dailyproduction_delete"),  # Страница удаления рапорта по его id
]