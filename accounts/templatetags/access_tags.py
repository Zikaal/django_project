from django import template

from accounts.utils import (
    can_access_dashboard,
    can_create_reports,
    can_delete_dailyproduction_obj,
    can_delete_reports,
    can_edit_dailyproduction_obj,
    can_edit_reports,
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

# Создаем экземпляр библиотеки тегов Django.
# Через него мы регистрируем свои фильтры и теги,
# которые потом можно использовать в шаблонах:
# {% load access_tags %}
register = template.Library()


@register.filter
def is_admin_role(user):
    """
    Проверяет, является ли пользователь администратором.

    Использование в шаблоне:
        {% load access_tags %}
        {% if request.user|is_admin_role %}
            ...
        {% endif %}
    """
    return is_admin(user)


@register.filter
def is_manager_role(user):
    """
    Проверяет, является ли пользователь менеджером.
    """
    return is_manager(user)


@register.filter
def is_operator_role(user):
    """
    Проверяет, является ли пользователь оператором.
    """
    return is_operator(user)


@register.filter
def can_manage_users_filter(user):
    """
    Может ли пользователь управлять пользователями.

    Обычно используется для показа/скрытия меню,
    кнопок редактирования и других admin-only элементов.
    """
    return can_manage_users(user)


@register.filter
def can_view_companies_filter(user):
    """
    Может ли пользователь просматривать компании.
    """
    return can_view_companies(user)


@register.filter
def can_manage_companies_filter(user):
    """
    Может ли пользователь управлять компаниями.
    """
    return can_manage_companies(user)


@register.filter
def can_view_wells_filter(user):
    """
    Может ли пользователь просматривать скважины.
    """
    return can_view_wells(user)


@register.filter
def can_manage_wells_filter(user):
    """
    Может ли пользователь управлять скважинами.
    """
    return can_manage_wells(user)


@register.filter
def can_view_reports_filter(user):
    """
    Может ли пользователь просматривать рапорты добычи.
    """
    return can_view_reports(user)


@register.filter
def can_create_reports_filter(user):
    """
    Может ли пользователь создавать рапорты добычи.
    """
    return can_create_reports(user)


@register.filter
def can_edit_reports_filter(user):
    """
    Может ли пользователь в целом редактировать рапорты добычи.

    Важно:
    это общая проверка по роли и permissions,
    без привязки к конкретному объекту.
    """
    return can_edit_reports(user)


@register.filter
def can_delete_reports_filter(user):
    """
    Может ли пользователь в целом удалять рапорты добычи.

    Это тоже общая permission-проверка,
    не object-level.
    """
    return can_delete_reports(user)


@register.filter
def can_import_export_filter(user):
    """
    Может ли пользователь пользоваться импортом/экспортом.
    """
    return can_import_export(user)


@register.filter
def can_access_dashboard_filter(user):
    """
    Может ли пользователь заходить в dashboard.
    """
    return can_access_dashboard(user)


@register.simple_tag
def can_edit_report_obj(user, report):
    """
    Object-level проверка:
    может ли пользователь редактировать конкретный report.

    Почему simple_tag, а не filter:
    - сюда передаются два аргумента: user и report;
    - filter обычно удобнее для одного основного значения.

    Использование в шаблоне:
        {% load access_tags %}
        {% can_edit_report_obj request.user report as can_edit %}
        {% if can_edit %}
            ...
        {% endif %}
    """
    return can_edit_dailyproduction_obj(user, report)


@register.simple_tag
def can_delete_report_obj(user, report):
    """
    Object-level проверка:
    может ли пользователь удалить конкретный report.

    Учитывает уже не только роль/permissions,
    но и ограничения на уровне объекта,
    например возраст рапорта для Operator.
    """
    return can_delete_dailyproduction_obj(user, report)
