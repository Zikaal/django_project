from django import forms
from django.contrib.auth import get_user_model

from .models import Profile

User = get_user_model()


class UserCreateForm(forms.ModelForm):
    """
    Форма для создания нового пользователя администратором.

    Расширяет стандартную ModelForm для модели User:
    - Добавляет поля для ввода и подтверждения пароля
    - Включает поля для создания связанного профиля (компания, отдел, телефон, bio)
    - Переопределяет методы clean() и save() для корректной обработки пароля и профиля
    """

    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput,
        help_text="Введите пароль"
    )
    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput,
        help_text="Повторите пароль"
    )

    # Поля, которые будут сохранены в модель Profile
    oil_company = forms.ModelChoiceField(
        queryset=Profile._meta.get_field("oil_company").related_model.objects.all(),
        label="Нефтяная компания",
        required=True,
    )
    department = forms.CharField(
        label="Отдел",
        max_length=150,
        required=False
    )
    phone_number = forms.CharField(
        label="Телефон",
        max_length=30,
        required=False
    )
    bio = forms.CharField(
        label="О себе",
        required=False,
        widget=forms.Textarea
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]

    def clean(self):
        """
        Дополнительная валидация формы.

        Проверяет совпадение введённых паролей.
        """
        cleaned_data = super().clean()

        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают.")

        return cleaned_data

    def save(self, commit=True):
        """
        Переопределённый метод сохранения.

        1. Создаёт пользователя с зашифрованным паролем
        2. Автоматически создаёт связанный профиль (Profile)
        3. Заполняет дополнительные поля профиля из формы

        Returns:
            User: созданный пользователь
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()
            # Создаём или получаем профиль и заполняем его данными
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.oil_company = self.cleaned_data["oil_company"]
            profile.department = self.cleaned_data.get("department", "")
            profile.phone_number = self.cleaned_data.get("phone_number", "")
            profile.bio = self.cleaned_data.get("bio", "")
            profile.save()

        return user


class UserUpdateForm(forms.ModelForm):
    """
    Форма для обновления основных данных пользователя.
    Используется при редактировании пользователя администратором.
    """

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]


class ProfileForm(forms.ModelForm):
    """
    Форма для редактирования профиля пользователя.
    Используется как в ProfileUpdateView, так и в комбинированном редактировании пользователя.
    """

    class Meta:
        model = Profile
        fields = ["oil_company", "department", "phone_number", "bio"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows":5}),
        }