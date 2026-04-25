from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Profile

# Получаем активную модель пользователя проекта.
User = get_user_model()

# Названия ролевых групп, которые считаются системными ролями приложения.
ROLE_GROUPS = ("Admin", "Manager", "Operator")


def _get_role(user) -> str:
    """
    Возвращает роль пользователя для отображения в Django Admin.

    Логика:
    - ищем первую группу пользователя среди системных ролей;
    - если группа найдена — возвращаем ее имя;
    - если нет — показываем прочерк.

    Где используется:
    - в list_display админки ProfileAdmin.
    """
    group = user.groups.filter(name__in=ROLE_GROUPS).first()
    return group.name if group else "—"


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Настройка админ-панели для модели Profile.

    Что дает:
    - удобное отображение профилей сотрудников;
    - быстрый поиск по ключевым полям;
    - фильтрацию по компании, отделу и группам пользователя;
    - сортировку по username.
    """

    # Колонки, которые показываются в списке профилей.
    list_display = (
        "id",
        "user",
        "get_role",
        "oil_company",
        "department",
        "phone_number",
    )

    # Поля, по которым работает поиск в админке.
    # Можно искать по username, отделу, телефону и названию компании.
    search_fields = (
        "user__username",
        "department",
        "phone_number",
        "oil_company__name",
    )

    # Фильтры справа в Django Admin.
    # user__groups позволяет фильтровать по ролям через связанные группы.
    list_filter = (
        "oil_company",
        "department",
        "user__groups",
    )

    # Сортировка по умолчанию.
    ordering = ("user__username",)

    @admin.display(description="Роль")
    def get_role(self, obj):
        """
        Возвращает роль пользователя для отображения в отдельной колонке админки.

        obj — это экземпляр Profile.
        Роль вычисляется через связанного пользователя.
        """
        return _get_role(obj.user)
