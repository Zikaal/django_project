from rest_framework.permissions import BasePermission

from accounts.utils import (
    get_user_company,
    is_admin,
    is_manager,
    is_operator,
)


class HasAnyBusinessRole(BasePermission):
    """
    Разрешает доступ только авторизованным пользователям
    с одной из бизнес-ролей системы:
    - Admin
    - Manager
    - Operator

    Подходит для API-методов, где анонимный доступ запрещен,
    а пользователь без роли не должен работать с бизнес-данными.
    """

    message = "У пользователя нет роли для работы с API."

    def has_permission(self, request, view):
        """
        Проверяет доступ на уровне всего endpoint.

        Возвращает True только если:
        - пользователь авторизован;
        - пользователь имеет одну из допустимых ролей.
        """
        user = request.user
        return (
            user
            and user.is_authenticated
            and (is_admin(user) or is_manager(user) or is_operator(user))
        )


class CanCreateDailyProduction(BasePermission):
    """
    Permission для создания суточного рапорта.

    По текущей логике:
    - Admin может создавать;
    - Manager может создавать;
    - Operator может создавать.

    Важно:
    этот permission не проверяет, к какой компании относится скважина.
    Такая бизнес-валидация вынесена в serializer, где уже есть доступ
    к входным данным и можно проверить well/company более точно.
    """

    message = "У вас нет прав для отправки суточного рапорта."

    def has_permission(self, request, view):
        """
        Проверяет только базовое право на создание рапорта.

        Это permission уровня endpoint, а не объекта.
        """
        user = request.user
        return (
            user
            and user.is_authenticated
            and (is_admin(user) or is_manager(user) or is_operator(user))
        )


class CanAccessOwnCompanyData(BasePermission):
    """
    Object-level permission для доступа к данным своей компании.

    Правила:
    - Admin видит все объекты;
    - Manager и Operator работают только с объектами своей компании.

    Поддерживаемые сценарии:
    - объект DailyProduction, где компания определяется через obj.well.oil_company_id;
    - объект Well, где компания определяется через obj.oil_company_id.
    """

    message = "Нет доступа к данным другой компании."

    def has_object_permission(self, request, view, obj):
        """
        Проверяет доступ к конкретному объекту.

        Алгоритм:
        1. Admin получает полный доступ.
        2. Для остальных берем компанию пользователя.
        3. Сравниваем компанию пользователя с компанией объекта.
        """
        user = request.user

        if is_admin(user):
            return True

        user_company = get_user_company(user)
        if user_company is None:
            return False

        # Сценарий для DailyProduction:
        # у объекта есть well, а у well — oil_company_id.
        if hasattr(obj, "well") and hasattr(obj.well, "oil_company_id"):
            return obj.well.oil_company_id == user_company.id

        # Сценарий для Well:
        # у объекта напрямую есть oil_company_id.
        if hasattr(obj, "oil_company_id"):
            return obj.oil_company_id == user_company.id

        # Если тип объекта не поддерживается, доступ запрещаем.
        return False