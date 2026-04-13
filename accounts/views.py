from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView

from companies.models import OilCompany

from .forms import ProfileForm, UserCreateForm, UserUpdateForm
from .mixins import AdminRequiredMixin
from .models import Profile
from .utils import get_user_company, is_admin

from .forms import (
    ProfileForm,
    SelfProfileForm,
    SelfUserUpdateForm,
    UserCreateForm,
    UserUpdateForm,
    ROLES_REQUIRING_COMPANY,
)

User = get_user_model()


class RegisterView(CreateView):
    """Публичная регистрация — без ролевых ограничений."""
    model = User
    form_class = UserCreationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("login")


class UserListView(AdminRequiredMixin, ListView):
    """
    Список пользователей — только для Admin.
    Manager и Operator не имеют доступа к управлению пользователями.
    """

    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    paginate_by = 20

    def get_queryset(self):
        queryset = (
            User.objects
            .select_related("profile", "profile__oil_company")
            .prefetch_related("groups")
        )

        sort = self.request.GET.get("sort", "username")
        company = self.request.GET.get("company", "")

        if company:
            queryset = queryset.filter(profile__oil_company_id=company)

        if sort == "-username":
            queryset = queryset.order_by("-username")
        elif sort == "company":
            queryset = queryset.order_by("profile__oil_company__name", "username")
        else:
            queryset = queryset.order_by("username")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["companies"] = OilCompany.objects.order_by("name")
        context["sort"] = self.request.GET.get("sort", "username")
        context["selected_company"] = self.request.GET.get("company", "")
        context["total_count"] = self.get_queryset().count()

        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["query_string"] = query_params.urlencode()

        return context


class UserCreateView(AdminRequiredMixin, CreateView):
    """
    Создание нового пользователя — только для Admin.
    Форма включает выбор роли (Admin / Manager / Operator).
    """

    model = User
    form_class = UserCreateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("user_list")


def user_update_view(request, pk):
    """
    Редактирование пользователя и его профиля.
    Доступно только Admin.
    """
    if not request.user.is_authenticated:
        from django.conf import settings
        from django.shortcuts import redirect as _redirect
        return _redirect(settings.LOGIN_URL)

    if not is_admin(request.user):
        raise PermissionDenied("Редактирование пользователей доступно только администраторам.")

    user = get_object_or_404(User, pk=pk)
    profile, _ = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

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
            "edited_user": user,
        },
    )


class UserDeleteView(AdminRequiredMixin, DeleteView):
    """Удаление пользователя — только для Admin."""

    model = User
    template_name = "accounts/user_confirm_delete.html"
    success_url = reverse_lazy("user_list")


class ProfileDetailView(LoginRequiredMixin, TemplateView):
    """Просмотр своего профиля — любой авторизованный пользователь."""
    template_name = "accounts/profile.html"


def profile_update_view(request):
    """Безопасное редактирование собственного профиля без смены роли и компании."""
    if not request.user.is_authenticated:
        from django.conf import settings
        return redirect(settings.LOGIN_URL)

    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        user_form = SelfUserUpdateForm(request.POST, instance=user)
        profile_form = SelfProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect("profile")
    else:
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