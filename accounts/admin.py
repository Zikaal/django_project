from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from .models import Profile

User = get_user_model()

ROLE_GROUPS = ("Admin", "Manager", "Operator")


def _get_role(user) -> str:
    """Возвращает название ролевой группы пользователя или '-'."""
    group = user.groups.filter(name__in=ROLE_GROUPS).first()
    return group.name if group else "—"


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Административная панель для модели Profile."""

    list_display = ("id", "user", "get_role", "oil_company", "department", "phone_number")
    search_fields = ("user__username", "department", "phone_number", "oil_company__name")
    list_filter = ("oil_company", "department", "user__groups")
    ordering = ("user__username",)

    @admin.display(description="Роль")
    def get_role(self, obj):
        return _get_role(obj.user)