from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView

from companies.models import OilCompany

from .forms import ProfileForm, UserCreateForm, UserUpdateForm
from .models import Profile

User = get_user_model()


class RegisterView(CreateView):
    """
    Представление для регистрации нового пользователя.

    Использует стандартную форму Django `UserCreationForm`.
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
    Поддерживает фильтрацию по компании, сортировку и пагинацию.
    """

    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    paginate_by = 20

    def get_queryset(self):
        """
        Переопределяем queryset для:
        1. Оптимизации запросов через select_related
        2. Фильтрации по нефтяной компании (GET-параметр "company")
        3. Сортировки по GET-параметру "sort"
        """
        queryset = User.objects.select_related("profile", "profile__oil_company")

        sort = self.request.GET.get("sort", "username")
        company = self.request.GET.get("company", "")

        # Фильтрация по компании
        if company:
            queryset = queryset.filter(profile__oil_company_id=company)

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
        Добавляем в контекст шаблона данные для фильтров и пагинации:
        - Список всех компаний для фильтра
        - Текущие значения сортировки и фильтра
        - Общее количество пользователей после фильтрации
        - Строку GET-параметров без 'page'
        """
        context = super().get_context_data(**kwargs)

        context["companies"] = OilCompany.objects.order_by("name")
        context["sort"] = self.request.GET.get("sort", "username")
        context["selected_company"] = self.request.GET.get("company", "")
        context["total_count"] = self.get_queryset().count()

        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["query_string"] = query_params.urlencode()

        return context


class UserCreateView(LoginRequiredMixin, CreateView):
    """
    Представление для создания нового пользователя администратором.
    Использует кастомную форму `UserCreateForm`.
    После успешного создания перенаправляет на список пользователей.
    """

    model = User
    form_class = UserCreateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("user_list")


def user_update_view(request, pk):
    """
    Функциональное представление для обновления пользователя и его профиля.

    Особенности:
    - Редактирует сразу две модели: User и Profile
    - Использует две отдельные формы (UserUpdateForm + ProfileForm)
    - При первом редактировании профиля автоматически создаёт запись Profile

    Args:
        request: HTTP-запрос
        pk: первичный ключ пользователя

    Returns:
        HttpResponse с формой или редирект на список пользователей после сохранения.
    """
    user = get_object_or_404(User, pk=pk)
    # Получаем или создаём профиль пользователя
    profile, _ = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect("user_list")
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileForm(instance=profile)

    return render(
        request,
        "accounts/user_form.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
            "edited_user": user,  # передаём для отображения информации в шаблоне
        },
    )


class UserDeleteView(LoginRequiredMixin, DeleteView):
    """
    Представление для удаления пользователя.
    Использует стандартный шаблон подтверждения удаления.
    После удаления перенаправляет на список пользователей.
    """

    model = User
    template_name = "accounts/user_confirm_delete.html"
    success_url = reverse_lazy("user_list")


class ProfileDetailView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"


def profile_update_view(request):
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect("profile")
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileForm(instance=profile)

    return render(
        request,
        "accounts/profile_form.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
        },
    )
