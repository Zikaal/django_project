from django import template

from accounts.utils import (
    can_access_dashboard,
    can_create_reports,
    can_delete_reports,
    can_delete_dailyproduction_obj,
    can_edit_reports,
    can_edit_dailyproduction_obj,
    can_import_export,
    can_manage_companies,
    can_manage_users,
    can_manage_wells,
    can_view_companies,
    can_view_reports,
    can_view_wells,
    is_admin,
    is_manager,
    is_operator,
)
register = template.Library()


@register.filter
def is_admin_role(user):
    return is_admin(user)


@register.filter
def is_manager_role(user):
    return is_manager(user)


@register.filter
def is_operator_role(user):
    return is_operator(user)


@register.filter
def can_manage_users_filter(user):
    return can_manage_users(user)


@register.filter
def can_view_companies_filter(user):
    return can_view_companies(user)


@register.filter
def can_manage_companies_filter(user):
    return can_manage_companies(user)


@register.filter
def can_view_wells_filter(user):
    return can_view_wells(user)


@register.filter
def can_manage_wells_filter(user):
    return can_manage_wells(user)


@register.filter
def can_view_reports_filter(user):
    return can_view_reports(user)


@register.filter
def can_create_reports_filter(user):
    return can_create_reports(user)


@register.filter
def can_edit_reports_filter(user):
    return can_edit_reports(user)


@register.filter
def can_delete_reports_filter(user):
    return can_delete_reports(user)


@register.filter
def can_import_export_filter(user):
    return can_import_export(user)


@register.filter
def can_access_dashboard_filter(user):
    return can_access_dashboard(user)

@register.simple_tag
def can_edit_report_obj(user, report):
    return can_edit_dailyproduction_obj(user, report)


@register.simple_tag
def can_delete_report_obj(user, report):
    return can_delete_dailyproduction_obj(user, report)