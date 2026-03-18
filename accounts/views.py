from django.contrib.auth import get_user_model  # Импортируем функцию для получения текущей модели пользователя
from django.contrib.auth.forms import UserCreationForm  # Импортируем встроенную форму Django для регистрации пользователя
from django.contrib.auth.mixins import LoginRequiredMixin  # Импортируем миксин для ограничения доступа только авторизованным пользователям
from django.urls import reverse_lazy  # Импортируем reverse_lazy для ленивого получения URL по имени маршрута
from django.views.generic import ListView  # Импортируем generic view для вывода списка объектов
from django.views.generic.edit import CreateView, UpdateView  # Импортируем generic views для создания и редактирования объектов

from .forms import ProfileForm  # Импортируем форму ProfileForm из текущего приложения
from .models import Profile  # Импортируем модель Profile из текущего приложения

User = get_user_model()  # Получаем текущую модель пользователя, используемую в проекте

class RegisterView(CreateView):  # Создаем view для регистрации нового пользователя
    model = User  # Указываем модель, с которой работает это представление
    form_class = UserCreationForm  # Указываем форму, которая будет использоваться для регистрации
    template_name = "registration/register.html"  # Указываем HTML-шаблон страницы регистрации
    success_url = reverse_lazy("login")  # После успешной регистрации перенаправляем пользователя на страницу входа

class UserListView(LoginRequiredMixin, ListView):  # Создаем view для отображения списка пользователей, доступное только авторизованным
    model = User  # Указываем модель, объекты которой будут выводиться в списке
    template_name = "accounts/user_list.html"  # Указываем HTML-шаблон страницы со списком пользователей
    context_object_name = "users"  # Задаем имя переменной, через которую список будет доступен в шаблоне

    def get_queryset(self):  # Переопределяем метод получения набора объектов для списка
        return User.objects.select_related("profile").order_by("username")  # Получаем всех пользователей вместе с их профилями и сортируем по username

class ProfileUpdateView(LoginRequiredMixin, UpdateView):  # Создаем view для редактирования профиля текущего пользователя
    model = Profile  # Указываем модель, которую будем редактировать
    form_class = ProfileForm  # Указываем форму для редактирования профиля
    template_name = "accounts/profile_form.html"  # Указываем HTML-шаблон страницы профиля
    success_url = reverse_lazy("profile")  # После успешного сохранения остаемся на странице профиля

    def get_object(self, queryset=None):  # Переопределяем метод, который возвращает редактируемый объект
        return self.request.user.profile  # Возвращаем профиль текущего авторизованного пользователя