from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from companies.models import OilCompany

from .models import Profile

User = get_user_model()

ROLE_CHOICES = [
    ("", "— Выберите роль —"),
    ("Admin", "Admin"),
    ("Manager", "Manager"),
    ("Operator", "Operator"),
]
ROLES_REQUIRING_COMPANY = {"Manager", "Operator"}


class UserCreateForm(forms.ModelForm):
    """Создание пользователя администратором."""

    password1 = forms.CharField(
        label="Пароль", widget=forms.PasswordInput, help_text="Введите пароль"
    )
    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput,
        help_text="Повторите пароль",
    )
    role = forms.ChoiceField(
        label="Роль",
        choices=ROLE_CHOICES,
        required=True,
        help_text="Admin — полный доступ, Manager — своя компания, Operator — рапорты своей компании",
    )
    oil_company = forms.ModelChoiceField(
        queryset=OilCompany.objects.order_by("name"),
        label="Нефтяная компания",
        required=False,
        help_text="Обязательно для Manager и Operator",
    )
    department = forms.CharField(label="Отдел", max_length=150, required=False)
    phone_number = forms.CharField(label="Телефон", max_length=30, required=False)
    bio = forms.CharField(label="О себе", required=False, widget=forms.Textarea)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]

    def clean(self):
        cleaned_data = super().clean()

        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают.")

        role = cleaned_data.get("role")
        if role and not Group.objects.filter(name=role).exists():
            raise forms.ValidationError(
                f"Группа «{role}» не найдена. Выполните: python manage.py create_groups"
            )

        if role in ROLES_REQUIRING_COMPANY and not cleaned_data.get("oil_company"):
            self.add_error(
                "oil_company",
                f"Для роли «{role}» необходимо выбрать нефтяную компанию.",
            )

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.oil_company = self.cleaned_data.get("oil_company")
            profile.department = self.cleaned_data.get("department", "")
            profile.phone_number = self.cleaned_data.get("phone_number", "")
            profile.bio = self.cleaned_data.get("bio", "")
            profile.save()
            _assign_role(user, self.cleaned_data.get("role"))

        return user


class UserUpdateForm(forms.ModelForm):
    """Редактирование пользователя администратором, включая роль."""

    role = forms.ChoiceField(
        label="Роль",
        choices=ROLE_CHOICES,
        required=False,
        help_text="Оставьте пустым, чтобы не менять текущую роль",
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            role_names = {choice[0] for choice in ROLE_CHOICES if choice[0]}
            current_group = self.instance.groups.filter(name__in=role_names).first()
            if current_group:
                self.fields["role"].initial = current_group.name

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            role = self.cleaned_data.get("role")
            if role:
                _assign_role(user, role)
        return user


class SelfUserUpdateForm(forms.ModelForm):
    """Безопасное редактирование собственных данных без смены роли."""

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]


class ProfileForm(forms.ModelForm):
    """Админская форма профиля, включает назначение компании."""

    class Meta:
        model = Profile
        fields = ["oil_company", "department", "phone_number", "bio", "avatar"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 5}),
        }


class SelfProfileForm(forms.ModelForm):
    """Безопасная форма собственного профиля без поля компании."""

    class Meta:
        model = Profile
        fields = ["department", "phone_number", "bio", "avatar"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 5}),
        }


def _assign_role(user, role_name: str) -> None:
    """Убирает пользователя из всех ролевых групп и добавляет в указанную."""
    if not role_name:
        return

    role_names = {choice[0] for choice in ROLE_CHOICES if choice[0]}
    user.groups.remove(*Group.objects.filter(name__in=role_names))

    try:
        group = Group.objects.get(name=role_name)
        user.groups.add(group)
    except Group.DoesNotExist:
        pass