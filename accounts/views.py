from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView

from companies.models import OilCompany

from .forms import (
    ProfileForm,
    SelfProfileForm,
    SelfUserUpdateForm,
    UserCreateForm,
    UserUpdateForm,
)
from .mixins import AdminRequiredMixin
from .models import Profile
from .utils import is_admin

# Получаем активную модель пользователя.
# Это правильный подход в Django, потому что проект может использовать
# как стандартную User-модель, так и кастомную.
User = get_user_model()


class RegisterView(CreateView):
    """
    Публичная регистрация пользователя.

    Что делает:
    - показывает стандартную форму регистрации Django;
    - создает нового пользователя;
    - после успешной регистрации отправляет на страницу логина.

    Важно:
    - здесь нет ограничений по ролям, это именно открытая регистрация;
    - используется встроенный UserCreationForm, поэтому логика простая и стандартная.
    """

    model = User
    form_class = UserCreationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("login")


class UserListView(AdminRequiredMixin, ListView):
    """
    Список пользователей системы.

    Доступ:
    - только для администратора;
    - доступ контролируется через AdminRequiredMixin.

    Что умеет:
    - выводить пользователей постранично;
    - подгружать связанные profile, oil_company и groups заранее,
      чтобы уменьшить количество SQL-запросов;
    - фильтровать пользователей по компании;
    - сортировать пользователей по имени или компании.
    """

    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    paginate_by = 20

    def get_queryset(self):
        """
        Формирует queryset для списка пользователей.

        Оптимизации:
        - select_related("profile", "profile__oil_company") нужен для OneToOne/ForeignKey,
          чтобы не делать отдельный запрос на каждый профиль и компанию;
        - prefetch_related("groups") нужен для M2M-групп пользователя.

        GET-параметры:
        - sort: способ сортировки;
        - company: фильтр по id нефтяной компании.
        """
        queryset = User.objects.select_related("profile", "profile__oil_company").prefetch_related("groups")

        # Параметр сортировки. По умолчанию сортируем по username.
        sort = self.request.GET.get("sort", "username")

        # Параметр фильтра по компании.
        company = self.request.GET.get("company", "")

        # Если компания выбрана — ограничиваем список пользователями этой компании.
        if company:
            queryset = queryset.filter(profile__oil_company_id=company)

        # Поддерживаем несколько вариантов сортировки.
        if sort == "-username":
            queryset = queryset.order_by("-username")
        elif sort == "company":
            queryset = queryset.order_by("profile__oil_company__name", "username")
        else:
            queryset = queryset.order_by("username")

        return queryset

    def get_context_data(self, **kwargs):
        """
        Добавляет в шаблон дополнительные данные для фильтров и пагинации.

        Передаем:
        - companies: список компаний для dropdown/select;
        - sort: текущая активная сортировка;
        - selected_company: выбранная компания;
        - total_count: общее количество пользователей после фильтрации;
        - query_string: текущие GET-параметры без page, чтобы пагинация
          не теряла фильтр и сортировку при переключении страниц.
        """
        context = super().get_context_data(**kwargs)

        context["companies"] = OilCompany.objects.order_by("name")
        context["sort"] = self.request.GET.get("sort", "username")
        context["selected_company"] = self.request.GET.get("company", "")
        context["total_count"] = self.get_queryset().count()

        # Убираем параметр page, чтобы при построении ссылок пагинации
        # не дублировать старый номер страницы.
        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["query_string"] = query_params.urlencode()

        return context


class UserCreateView(AdminRequiredMixin, CreateView):
    """
    Создание нового пользователя администратором.

    Доступ:
    - только для администратора.

    Особенности:
    - используется кастомная форма UserCreateForm;
    - форма уже умеет создавать профиль и назначать роль;
    - после успешного создания происходит переход к списку пользователей.
    """

    model = User
    form_class = UserCreateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("user_list")


def user_update_view(request, pk):
    """
    Редактирование пользователя и его профиля.

    Почему function-based view, а не class-based:
    - здесь одновременно редактируются две формы:
      1) данные User
      2) данные Profile
    - для такого сценария FBV часто проще и нагляднее.

    Доступ:
    - только для администратора.

    Логика:
    - если пользователь не авторизован, отправляем на login;
    - если роль не admin, выбрасываем PermissionDenied;
    - загружаем пользователя по pk;
    - если профиля нет, создаем его через get_or_create;
    - на POST валидируем обе формы;
    - сохраняем обе только если обе валидны;
    - после успеха возвращаемся к списку пользователей.
    """
    # Если пользователь не вошел в систему — перенаправляем на страницу логина.
    if not request.user.is_authenticated:
        from django.conf import settings
        from django.shortcuts import redirect as _redirect

        return _redirect(settings.LOGIN_URL)

    # Дополнительная проверка роли.
    # Даже если URL кто-то знает, без admin-доступа изменить пользователя нельзя.
    if not is_admin(request.user):
        raise PermissionDenied("Редактирование пользователей доступно только администраторам.")

    # Получаем редактируемого пользователя или 404, если такого pk нет.
    user = get_object_or_404(User, pk=pk)

    # Гарантируем наличие профиля.
    # Это полезно на случай старых пользователей или неполных данных в БД.
    profile, _ = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        # Передаем POST-данные в формы.
        # request.FILES нужен для загрузки аватара и других файлов профиля.
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

        # Сохраняем только если обе формы валидны.
        # Это защищает от ситуации, когда User сохранился, а Profile — нет.
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect("user_list")
    else:
        # GET-запрос: показываем формы, заполненные текущими значениями.
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileForm(instance=profile)

    # Рендерим страницу редактирования.
    return render(
        request,
        "accounts/user_form.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
            "edited_user": user,  # часто используется в шаблоне для заголовка "Редактирование ..."
        },
    )


class UserDeleteView(AdminRequiredMixin, DeleteView):
    """
    Удаление пользователя.

    Доступ:
    - только для администратора.

    Поведение:
    - показывает страницу подтверждения удаления;
    - после подтверждения удаляет пользователя;
    - затем возвращает в список пользователей.
    """

    model = User
    template_name = "accounts/user_confirm_delete.html"
    success_url = reverse_lazy("user_list")


class ProfileDetailView(LoginRequiredMixin, TemplateView):
    """
    Просмотр собственного профиля.

    Доступ:
    - любой авторизованный пользователь.

    Замечание:
    - это TemplateView, потому что здесь нет сложной серверной логики;
    - шаблон сам может брать данные через request.user и request.user.profile.
    """

    template_name = "accounts/profile.html"


def profile_update_view(request):
    """
    Редактирование собственного профиля текущим пользователем.

    Важное отличие от admin-редактирования:
    - пользователь может менять только свои безопасные данные;
    - он НЕ может менять себе роль;
    - он НЕ может менять себе компанию.

    Используются формы:
    - SelfUserUpdateForm — только базовые поля пользователя;
    - SelfProfileForm — только разрешенные поля профиля.

    Это защищает систему от самовольного повышения прав или смены компании.
    """
    # Если пользователь не авторизован — отправляем на login.
    if not request.user.is_authenticated:
        from django.conf import settings

        return redirect(settings.LOGIN_URL)

    # Работаем только с текущим пользователем.
    user = request.user

    # Если профиль еще не существует — создаем.
    profile, _ = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        # Обновляем только разрешенные для самого пользователя поля.
        user_form = SelfUserUpdateForm(request.POST, instance=user)
        profile_form = SelfProfileForm(request.POST, request.FILES, instance=profile)

        # Обе формы должны быть валидны, иначе ничего не сохраняем.
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect("profile")
    else:
        # GET-запрос: открываем форму с текущими данными пользователя.
        user_form = SelfUserUpdateForm(instance=user)
        profile_form = SelfProfileForm(instance=profile)

    return render(
        request,
        "accounts/profile_form.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
        },
    )
