from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView

from .forms import ProfileForm
from .models import Profile

# Получаем модель пользователя (на случай, если используется кастомная модель User)
User = get_user_model()


class RegisterView(CreateView):
    """
    Представление для регистрации нового пользователя.

    Использует стандартную форму Django UserCreationForm.
    После успешной регистрации перенаправляет пользователя на страницу входа.
    """

    model = User
    form_class = UserCreationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("login")


class UserListView(LoginRequiredMixin, ListView):
    """
    Представление для отображения списка всех пользователей системы.

    Доступно только авторизованным пользователям.
    Поддерживает пагинацию, сортировку и оптимизацию запросов к связанным данным.
    """

    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"   # имя переменной в шаблоне
    paginate_by = 20                # количество пользователей на странице

    def get_queryset(self):
        """
        Переопределяем queryset для:
        1. Оптимизации запросов через select_related (загружаем Profile и OilCompany заранее)
        2. Применения сортировки по GET-параметру 'sort'
        """
        sort = self.request.GET.get("sort", "username")

        # Оптимизация: загружаем связанные объекты за один запрос
        queryset = User.objects.select_related("profile", "profile__oil_company")

        # Применяем сортировку
        if sort == "-username":
            queryset = queryset.order_by("-username")
        elif sort == "company":
            queryset = queryset.order_by("profile__oil_company__name", "username")
        else:
            # Сортировка по умолчанию — по имени пользователя
            queryset = queryset.order_by("username")

        return queryset

    def get_context_data(self, **kwargs):
        """
        Добавляем в контекст шаблона дополнительные данные:
        - Текущий выбранный тип сортировки
        - Общее количество пользователей в системе
        - Строку GET-параметров без 'page' (для корректной пагинации при сортировке)
        """
        context = super().get_context_data(**kwargs)

        context["sort"] = self.request.GET.get("sort", "username")
        context["total_count"] = User.objects.count()

        # Сохраняем все GET-параметры кроме 'page'
        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["query_string"] = query_params.urlencode()

        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """
    Представление для редактирования профиля текущего пользователя.

    Важные особенности:
    - Пользователь может редактировать только свой собственный профиль
    - Метод get_object переопределён, чтобы всегда возвращать профиль текущего пользователя
    - После успешного обновления перенаправляет на страницу профиля
    """

    model = Profile
    form_class = ProfileForm
    template_name = "accounts/profile_form.html"
    success_url = reverse_lazy("profile")

    def get_object(self, queryset=None):
        """
        Возвращает профиль текущего авторизованного пользователя.

        Переопределяем стандартное поведение, чтобы пользователь не мог
        редактировать профиль другого пользователя по pk в URL.
        """
        return self.request.user.profile