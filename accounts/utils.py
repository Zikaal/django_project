from __future__ import annotations

from collections.abc import Iterable
from datetime import timedelta
from typing import TYPE_CHECKING

from django.utils import timezone

# TYPE_CHECKING нужен, чтобы использовать типы только для подсказок/линтеров,
# не создавая циклические импорты во время выполнения.
if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

    from companies.models import OilCompany


# Константы ролей, используемых в проекте.
# Важно: названия должны совпадать с названиями групп в Django.
ROLE_ADMIN = "Admin"
ROLE_MANAGER = "Manager"
ROLE_OPERATOR = "Operator"

# Множество всех допустимых ролевых групп.
ROLE_NAMES = {ROLE_ADMIN, ROLE_MANAGER, ROLE_OPERATOR}


def _is_authenticated(user: AbstractBaseUser | None) -> bool:
    """
    Безопасно проверяет, авторизован ли пользователь.

    Почему отдельная функция:
    - позволяет централизованно обрабатывать None;
    - избавляет остальной код от повторяющихся проверок;
    - делает permission-логику более читаемой.
    """
    return bool(user and getattr(user, "is_authenticated", False))


def _cached_role_names(user: AbstractBaseUser) -> set[str]:
    """
    Возвращает множество названий групп пользователя с кэшированием на объекте user.

    Зачем нужен кэш:
    - в течение одного request мы можем много раз вызывать проверки ролей;
    - без кэша каждый вызов снова делал бы запрос к БД;
    - с кэшем роли читаются один раз и дальше используются из памяти.

    Примечание:
    - кэш живет только на текущем объекте user в рамках текущего запроса.
    """
    if not hasattr(user, "_cached_role_names"):
        user._cached_role_names = set(user.groups.values_list("name", flat=True))
    return user._cached_role_names


def _cached_permissions(user: AbstractBaseUser) -> set[str]:
    """
    Возвращает кэшированный набор всех permission-кодов пользователя.

    Пример permission-кода:
    - 'companies.view_oilcompany'
    - 'productions.change_dailyproduction'

    Зачем нужен кэш:
    - user.get_all_permissions() может вызываться часто;
    - кэширование уменьшает количество повторных вычислений.
    """
    if not hasattr(user, "_cached_permissions"):
        user._cached_permissions = user.get_all_permissions()
    return user._cached_permissions


def has_all_permissions(user: AbstractBaseUser, permissions: Iterable[str] | None) -> bool:
    """
    Проверяет, есть ли у пользователя ВСЕ указанные permissions.

    Логика:
    - неавторизованный пользователь -> False;
    - пустой список permissions -> True;
    - иначе проверяем наличие каждого permission в кэше.

    Пример:
        has_all_permissions(user, ["companies.view_oilcompany", "companies.add_oilcompany"])
    """
    if not _is_authenticated(user):
        return False

    # Убираем пустые значения, если они случайно попали в список.
    permissions = tuple(perm for perm in (permissions or ()) if perm)

    # Если permissions не переданы, считаем, что дополнительных ограничений нет.
    if not permissions:
        return True

    cached = _cached_permissions(user)
    return all(perm in cached for perm in permissions)


def has_any_role(user: AbstractBaseUser) -> bool:
    """
    Проверяет, есть ли у пользователя хотя бы одна из системных ролей:
    Admin / Manager / Operator.

    Особый случай:
    - superuser автоматически считается имеющим роль.
    """
    if not _is_authenticated(user):
        return False
    if user.is_superuser:
        return True
    return bool(_cached_role_names(user) & ROLE_NAMES)


def is_admin(user: AbstractBaseUser) -> bool:
    """
    Проверяет, является ли пользователь администратором.

    Особый случай:
    - superuser всегда считается администратором,
      даже если формально не состоит в группе Admin.
    """
    if not _is_authenticated(user):
        return False
    if user.is_superuser:
        return True
    return ROLE_ADMIN in _cached_role_names(user)


def is_manager(user: AbstractBaseUser) -> bool:
    """
    Проверяет, состоит ли пользователь в группе Manager.
    """
    if not _is_authenticated(user):
        return False
    return ROLE_MANAGER in _cached_role_names(user)


def is_operator(user: AbstractBaseUser) -> bool:
    """
    Проверяет, состоит ли пользователь в группе Operator.
    """
    if not _is_authenticated(user):
        return False
    return ROLE_OPERATOR in _cached_role_names(user)


def get_user_role(user: AbstractBaseUser) -> str:
    """
    Возвращает основную роль пользователя в виде строки.

    Порядок важен:
    - сначала проверяем Admin;
    - потом Manager;
    - потом Operator.

    Это полезно, если по какой-то причине пользователь состоит сразу в нескольких группах.
    Тогда приоритет будет у Admin.
    """
    if is_admin(user):
        return ROLE_ADMIN
    if is_manager(user):
        return ROLE_MANAGER
    if is_operator(user):
        return ROLE_OPERATOR
    return "Unknown"


def get_user_company(user: AbstractBaseUser) -> OilCompany | None:
    """
    Возвращает компанию пользователя из его профиля.

    Правила:
    - неавторизованный пользователь -> None;
    - admin -> None, потому что админ не ограничен одной компанией;
    - если профиль/компания отсутствуют -> None.

    Используется для company-scoped доступа:
    когда менеджер или оператор должен видеть данные только своей компании.
    """
    if not _is_authenticated(user):
        return None

    # Администратор не привязан к одной компании.
    if is_admin(user):
        return None

    # Повторно используем закэшированное значение, если оно уже вычислялось.
    if hasattr(user, "_cached_oil_company"):
        return user._cached_oil_company

    try:
        profile = user.profile
    except Exception:
        # Если профиль не найден или произошла ошибка доступа,
        # безопасно сохраняем None в кэш.
        user._cached_oil_company = None
        return None

    user._cached_oil_company = profile.oil_company
    return user._cached_oil_company


def get_user_company_id(user: AbstractBaseUser) -> int | None:
    """
    Возвращает id компании пользователя или None.

    Это небольшая helper-функция для фильтрации queryset'ов,
    чтобы не вытаскивать объект компании целиком там, где нужен только id.
    """
    company = get_user_company(user)
    return company.id if company else None


def can_manage_users(user: AbstractBaseUser) -> bool:
    """
    Может ли пользователь управлять другими пользователями.

    В текущей бизнес-логике:
    - только Admin.
    """
    return is_admin(user)


def can_view_companies(user: AbstractBaseUser) -> bool:
    """
    Может ли пользователь просматривать список/детали компаний.

    Требования:
    - роль Admin или Manager;
    - наличие permission 'companies.view_oilcompany'.
    """
    return (is_admin(user) or is_manager(user)) and has_all_permissions(user, ["companies.view_oilcompany"])


def can_manage_companies(user: AbstractBaseUser) -> bool:
    """
    Может ли пользователь полностью управлять компаниями.

    Требования:
    - только Admin;
    - полный набор CRUD permissions для модели OilCompany.
    """
    return is_admin(user) and has_all_permissions(
        user,
        [
            "companies.view_oilcompany",
            "companies.add_oilcompany",
            "companies.change_oilcompany",
            "companies.delete_oilcompany",
        ],
    )


def can_view_wells(user: AbstractBaseUser) -> bool:
    """
    Может ли пользователь просматривать скважины.

    Требования:
    - Admin или Manager;
    - permission 'productions.view_well'.
    """
    return (is_admin(user) or is_manager(user)) and has_all_permissions(user, ["productions.view_well"])


def can_manage_wells(user: AbstractBaseUser) -> bool:
    """
    Может ли пользователь создавать/редактировать/удалять скважины.

    Требования:
    - Admin или Manager;
    - полный набор CRUD permissions для модели Well.
    """
    return (is_admin(user) or is_manager(user)) and has_all_permissions(
        user,
        [
            "productions.view_well",
            "productions.add_well",
            "productions.change_well",
            "productions.delete_well",
        ],
    )


def can_view_reports(user: AbstractBaseUser) -> bool:
    """
    Может ли пользователь просматривать рапорты добычи.

    Требования:
    - у пользователя должна быть хотя бы одна системная роль;
    - permission 'productions.view_dailyproduction'.
    """
    return has_any_role(user) and has_all_permissions(user, ["productions.view_dailyproduction"])


def can_create_reports(user: AbstractBaseUser) -> bool:
    """
    Может ли пользователь создавать рапорты добычи.

    Требования:
    - любая системная роль;
    - permission 'productions.add_dailyproduction'.
    """
    return has_any_role(user) and has_all_permissions(user, ["productions.add_dailyproduction"])


def can_edit_reports(user: AbstractBaseUser) -> bool:
    """
    Может ли пользователь редактировать рапорты добычи.

    Требования:
    - любая системная роль;
    - permission 'productions.change_dailyproduction'.
    """
    return has_any_role(user) and has_all_permissions(user, ["productions.change_dailyproduction"])


def can_delete_reports(user: AbstractBaseUser) -> bool:
    """
    Может ли пользователь удалять рапорты добычи.

    Требования:
    - любая системная роль;
    - permission 'productions.delete_dailyproduction'.
    """
    return has_any_role(user) and has_all_permissions(user, ["productions.delete_dailyproduction"])


def can_import_export(user: AbstractBaseUser) -> bool:
    """
    Может ли пользователь выполнять импорт/экспорт данных.

    В текущей логике:
    - только Admin и Manager;
    - достаточно permission на просмотр рапортов.

    Примечание:
    - если позже понадобится более строгая модель безопасности,
      можно завести отдельные permissions для import/export.
    """
    return (is_admin(user) or is_manager(user)) and has_all_permissions(user, ["productions.view_dailyproduction"])


def can_access_dashboard(user: AbstractBaseUser) -> bool:
    """
    Может ли пользователь заходить в dashboard.

    Требования:
    - роль Admin или Manager;
    - набор permissions для сущностей, которые используются на дашборде.

    Идея:
    - если дашборд агрегирует компании, скважины, рапорты и профили,
      то доступ к нему должен требовать права на чтение этих данных.
    """
    return (is_admin(user) or is_manager(user)) and has_all_permissions(
        user,
        [
            "companies.view_oilcompany",
            "productions.view_well",
            "productions.view_dailyproduction",
            "accounts.view_profile",
        ],
    )


def is_report_older_than_7_days(report) -> bool:
    """
    Проверяет, старше ли рапорт 7 дней.

    Используется для ограничения операторов:
    - оператор не должен менять слишком старые данные.

    Логика:
    - если report или report.date отсутствуют -> False;
    - иначе сравниваем дату рапорта с текущей локальной датой.
    """
    if not report or not report.date:
        return False

    today = timezone.localdate()
    return report.date < (today - timedelta(days=7))


def can_edit_dailyproduction_obj(user, report) -> bool:
    """
    Проверяет, можно ли пользователю редактировать конкретный объект DailyProduction.

    Общая логика:
    1. Сначала проверяем базовое право на редактирование рапортов.
    2. Если пользователь Operator и рапорт старше 7 дней — запрещаем.
    3. Во всех остальных случаях разрешаем.

    Это пример object-level permission,
    когда решение зависит не только от роли пользователя,
    но и от состояния конкретного объекта.
    """
    if not can_edit_reports(user):
        return False

    if is_operator(user) and is_report_older_than_7_days(report):
        return False

    return True


def can_delete_dailyproduction_obj(user, report) -> bool:
    """
    Проверяет, можно ли пользователю удалить конкретный объект DailyProduction.

    Логика аналогична редактированию:
    - базовое permission на удаление обязательно;
    - Operator не может удалять рапорты старше 7 дней.
    """
    if not can_delete_reports(user):
        return False

    if is_operator(user) and is_report_older_than_7_days(report):
        return False

    return True
