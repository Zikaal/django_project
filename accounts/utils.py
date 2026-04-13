from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from datetime import timedelta
from django.utils import timezone

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser
    from companies.models import OilCompany


ROLE_ADMIN = "Admin"
ROLE_MANAGER = "Manager"
ROLE_OPERATOR = "Operator"
ROLE_NAMES = {ROLE_ADMIN, ROLE_MANAGER, ROLE_OPERATOR}


def _is_authenticated(user: "AbstractBaseUser | None") -> bool:
    return bool(user and getattr(user, "is_authenticated", False))


def has_all_permissions(user: "AbstractBaseUser", permissions: Iterable[str] | None) -> bool:
    if not _is_authenticated(user):
        return False

    permissions = tuple(perm for perm in (permissions or ()) if perm)
    if not permissions:
        return True

    return user.has_perms(permissions)


def has_any_role(user: "AbstractBaseUser") -> bool:
    if not _is_authenticated(user):
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=ROLE_NAMES).exists()


def is_admin(user: "AbstractBaseUser") -> bool:
    if not _is_authenticated(user):
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=ROLE_ADMIN).exists()


def is_manager(user: "AbstractBaseUser") -> bool:
    if not _is_authenticated(user):
        return False
    return user.groups.filter(name=ROLE_MANAGER).exists()


def is_operator(user: "AbstractBaseUser") -> bool:
    if not _is_authenticated(user):
        return False
    return user.groups.filter(name=ROLE_OPERATOR).exists()


def get_user_role(user: "AbstractBaseUser") -> str:
    if is_admin(user):
        return ROLE_ADMIN
    if is_manager(user):
        return ROLE_MANAGER
    if is_operator(user):
        return ROLE_OPERATOR
    return "Unknown"


def get_user_company(user: "AbstractBaseUser") -> "OilCompany | None":
    if not _is_authenticated(user):
        return None
    if is_admin(user):
        return None

    try:
        return user.profile.oil_company
    except Exception:
        return None


def get_user_company_id(user: "AbstractBaseUser") -> int | None:
    company = get_user_company(user)
    return company.id if company else None


def can_manage_users(user: "AbstractBaseUser") -> bool:
    return is_admin(user)


def can_view_companies(user: "AbstractBaseUser") -> bool:
    return (is_admin(user) or is_manager(user)) and has_all_permissions(
        user, ["companies.view_oilcompany"]
    )


def can_manage_companies(user: "AbstractBaseUser") -> bool:
    return is_admin(user) and has_all_permissions(
        user,
        [
            "companies.view_oilcompany",
            "companies.add_oilcompany",
            "companies.change_oilcompany",
            "companies.delete_oilcompany",
        ],
    )


def can_view_wells(user: "AbstractBaseUser") -> bool:
    return (is_admin(user) or is_manager(user)) and has_all_permissions(
        user, ["productions.view_well"]
    )


def can_manage_wells(user: "AbstractBaseUser") -> bool:
    return (is_admin(user) or is_manager(user)) and has_all_permissions(
        user,
        [
            "productions.view_well",
            "productions.add_well",
            "productions.change_well",
            "productions.delete_well",
        ],
    )


def can_view_reports(user: "AbstractBaseUser") -> bool:
    return has_any_role(user) and has_all_permissions(
        user, ["productions.view_dailyproduction"]
    )


def can_create_reports(user: "AbstractBaseUser") -> bool:
    return has_any_role(user) and has_all_permissions(
        user, ["productions.add_dailyproduction"]
    )


def can_edit_reports(user: "AbstractBaseUser") -> bool:
    return has_any_role(user) and has_all_permissions(
        user, ["productions.change_dailyproduction"]
    )


def can_delete_reports(user: "AbstractBaseUser") -> bool:
    return has_any_role(user) and has_all_permissions(
        user, ["productions.delete_dailyproduction"]
    )


def can_import_export(user: "AbstractBaseUser") -> bool:
    return (is_admin(user) or is_manager(user)) and has_all_permissions(
        user, ["productions.view_dailyproduction"]
    )


def can_access_dashboard(user: "AbstractBaseUser") -> bool:
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
    if not report or not report.date:
        return False
    today = timezone.localdate()
    return report.date < (today - timedelta(days=7))


def can_edit_dailyproduction_obj(user, report) -> bool:
    if not can_edit_reports(user):
        return False

    if is_operator(user) and is_report_older_than_7_days(report):
        return False

    return True


def can_delete_dailyproduction_obj(user, report) -> bool:
    if not can_delete_reports(user):
        return False

    if is_operator(user) and is_report_older_than_7_days(report):
        return False

    return True