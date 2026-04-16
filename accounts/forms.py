from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from companies.models import OilCompany

from .models import Profile

# Получаем активную модель пользователя проекта.
# Это безопаснее, чем напрямую импортировать django.contrib.auth.models.User,
# потому что в проекте может использоваться кастомная User-модель.
User = get_user_model()

# Варианты ролей, которые доступны в системе.
# Первый пустой вариант нужен для отображения placeholder в select.
ROLE_CHOICES = [
    ("", "— Выберите роль —"),
    ("Admin", "Admin"),
    ("Manager", "Manager"),
    ("Operator", "Operator"),
]

# Роли, для которых обязательно должна быть указана нефтяная компания.
# Например:
# - Manager работает в рамках своей компании;
# - Operator тоже привязан к конкретной компании.
ROLES_REQUIRING_COMPANY = {"Manager", "Operator"}


class UserCreateForm(forms.ModelForm):
    """
    Форма создания пользователя администратором.

    Что делает:
    - создает базового пользователя (username, имя, email и т.д.);
    - проверяет совпадение паролей;
    - проверяет корректность выбранной роли;
    - требует компанию для Manager и Operator;
    - создает/обновляет профиль пользователя;
    - назначает пользователя в нужную группу (роль).

    Это не публичная регистрация, а именно административная форма создания.
    """

    # Первый пароль.
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput,
        help_text="Введите пароль",
    )

    # Повторный ввод пароля для защиты от опечаток.
    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput,
        help_text="Повторите пароль",
    )

    # Выбор роли пользователя.
    role = forms.ChoiceField(
        label="Роль",
        choices=ROLE_CHOICES,
        required=True,
        help_text="Admin — полный доступ, Manager — своя компания, Operator — рапорты своей компании",
    )

    # Компания задается отдельно, потому что хранится не в User, а в Profile.
    oil_company = forms.ModelChoiceField(
        queryset=OilCompany.objects.order_by("name"),
        label="Нефтяная компания",
        required=False,
        help_text="Обязательно для Manager и Operator",
    )

    # Дополнительные поля профиля.
    department = forms.CharField(label="Отдел", max_length=150, required=False)
    phone_number = forms.CharField(label="Телефон", max_length=30, required=False)
    bio = forms.CharField(label="О себе", required=False, widget=forms.Textarea)

    class Meta:
        model = User
        # Базовые поля модели пользователя.
        fields = ["username", "first_name", "last_name", "email"]

    def clean(self):
        """
        Общая валидация формы.

        Проверяем:
        - совпадают ли пароли;
        - существует ли выбранная ролевая группа в Django Groups;
        - выбрана ли компания, если роль этого требует.

        Почему проверка группы важна:
        - форма ожидает, что роли уже существуют в БД как Group;
        - если групп нет, назначить роль не получится.
        """
        cleaned_data = super().clean()

        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        # Пользователь должен ввести одинаковые пароли.
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают.")

        role = cleaned_data.get("role")

        # Проверяем, что соответствующая группа уже создана в системе.
        if role and not Group.objects.filter(name=role).exists():
            raise forms.ValidationError(
                f"Группа «{role}» не найдена. Выполните: python manage.py create_groups"
            )

        # Для некоторых ролей компания обязательна.
        if role in ROLES_REQUIRING_COMPANY and not cleaned_data.get("oil_company"):
            self.add_error(
                "oil_company",
                f"Для роли «{role}» необходимо выбрать нефтяную компанию.",
            )

        return cleaned_data

    def save(self, commit=True):
        """
        Сохраняет пользователя, профиль и роль.

        Порядок действий:
        1. Создаем объект user, но пока не сохраняем.
        2. Хэшируем пароль через set_password().
        3. Сохраняем пользователя.
        4. Создаем/обновляем профиль.
        5. Назначаем роль через Django Group.

        Важно:
        - пароль нельзя сохранять как обычный текст;
        - set_password() превращает пароль в безопасный хэш.
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

            # У каждого пользователя должен быть профиль.
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.oil_company = self.cleaned_data.get("oil_company")
            profile.department = self.cleaned_data.get("department", "")
            profile.phone_number = self.cleaned_data.get("phone_number", "")
            profile.bio = self.cleaned_data.get("bio", "")
            profile.save()

            # Назначаем выбранную роль.
            _assign_role(user, self.cleaned_data.get("role"))

        return user


class UserUpdateForm(forms.ModelForm):
    """
    Форма редактирования пользователя администратором.

    Что можно менять:
    - username, имя, фамилию, email;
    - роль пользователя.

    Особенность:
    - роль не обязательно менять каждый раз;
    - если роль оставлена пустой, текущая роль пользователя сохраняется.
    """

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
        """
        При открытии формы подставляем текущую роль пользователя в поле role.

        Это делает форму удобнее:
        - админ сразу видит текущую роль;
        - не нужно вспоминать, в какой группе состоит пользователь.
        """
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            role_names = {choice[0] for choice in ROLE_CHOICES if choice[0]}
            current_group = self.instance.groups.filter(name__in=role_names).first()
            if current_group:
                self.fields["role"].initial = current_group.name

    def save(self, commit=True):
        """
        Сохраняет базовые поля пользователя и, при необходимости, обновляет роль.
        """
        user = super().save(commit=commit)

        if commit:
            role = self.cleaned_data.get("role")
            if role:
                _assign_role(user, role)

        return user


class SelfUserUpdateForm(forms.ModelForm):
    """
    Безопасная форма редактирования собственного аккаунта.

    Для чего нужна отдельная форма:
    - пользователь может менять только личные данные;
    - пользователь НЕ должен через эту форму менять роль или системные права.
    """

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]


class ProfileForm(forms.ModelForm):
    """
    Админская форма профиля.

    Используется, когда администратор редактирует чужой профиль.
    Здесь можно менять и компанию, и остальные поля профиля.
    """

    class Meta:
        model = Profile
        fields = ["oil_company", "department", "phone_number", "bio", "avatar"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 5}),
        }


class SelfProfileForm(forms.ModelForm):
    """
    Безопасная форма редактирования собственного профиля.

    Отличие от ProfileForm:
    - поле oil_company намеренно исключено;
    - пользователь не может сам менять компанию, к которой он привязан.
    """

    class Meta:
        model = Profile
        fields = ["department", "phone_number", "bio", "avatar"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 5}),
        }


def _assign_role(user, role_name: str) -> None:
    """
    Назначает пользователю одну ролевую группу.

    Логика:
    - сначала удаляем пользователя из всех системных ролей;
    - затем добавляем в выбранную группу.

    Почему так:
    - система предполагает, что у пользователя должна быть одна основная роль;
    - это предотвращает конфликтные состояния вроде Admin + Operator одновременно.

    Если группа не найдена:
    - функция молча ничего не делает;
    - это защищает от падения приложения, но обычно лучше,
      чтобы группы были заранее созданы командой инициализации.
    """
    if not role_name:
        return

    role_names = {choice[0] for choice in ROLE_CHOICES if choice[0]}

    # Удаляем пользователя из всех ролевых групп проекта.
    user.groups.remove(*Group.objects.filter(name__in=role_names))

    try:
        group = Group.objects.get(name=role_name)
        user.groups.add(group)
    except Group.DoesNotExist:
        # Защита от ошибки, если группа не создана в БД.
        pass