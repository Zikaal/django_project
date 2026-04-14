from rest_framework.permissions import BasePermission

from accounts.utils import (
    is_admin,
    is_manager,
    is_operator,
    get_user_company,
)


class HasAnyBusinessRole(BasePermission):
    """
    Пользователь должен быть авторизован и иметь одну из ролей:
    Admin / Manager / Operator
    """

    message = "У пользователя нет роли для работы с API."

    def has_permission(self, request, view):
        user = request.user
        return (
            user
            and user.is_authenticated
            and (is_admin(user) or is_manager(user) or is_operator(user))
        )


class CanCreateDailyProduction(BasePermission):
    """
    Разрешает создание суточного рапорта только пользователям
    с ролью Admin / Manager / Operator.
    Дополнительная проверка скважины и компании остается в serializer.
    """

    message = "У вас нет прав для отправки суточного рапорта."

    def has_permission(self, request, view):
        user = request.user
        return (
            user
            and user.is_authenticated
            and (is_admin(user) or is_manager(user) or is_operator(user))
        )


class CanAccessOwnCompanyData(BasePermission):
    """
    Базовый объектный permission:
    Admin — доступ ко всему
    Manager / Operator — только к объектам своей компании
    """

    message = "Нет доступа к данным другой компании."

    def has_object_permission(self, request, view, obj):
        user = request.user

        if is_admin(user):
            return True

        user_company = get_user_company(user)
        if user_company is None:
            return False

        # Для DailyProduction
        if hasattr(obj, "well") and hasattr(obj.well, "oil_company_id"):
            return obj.well.oil_company_id == user_company.id

        # Для Well
        if hasattr(obj, "oil_company_id"):
            return obj.oil_company_id == user_company.id

        return False