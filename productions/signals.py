from decimal import Decimal

from django.conf import settings
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from accounts.current_user import get_current_user
from accounts.models import Profile
from companies.models import OilCompany
from .models import DailyProduction, ProductionAuditLog, Well
from django.db import transaction


AUDITED_FIELDS = (
    "work_time",
    "liquid_debit",
    "water_cut",
    "oil_density",
)

AUDITED_FIELD_LABELS = {
    "work_time": "Время работы, часов",
    "liquid_debit": "Дебит жидкости, м³/сут",
    "water_cut": "Обводненность, %",
    "oil_density": "Плотность нефти, т/м³",
}


def _bump_cache_version(key_name: str):
    try:
        current_value = cache.get(key_name)
        if current_value is None:
            cache.set(key_name, 1, None)
        else:
            cache.incr(key_name)
    except ValueError:
        cache.set(key_name, 2, None)
    except Exception:
        pass


def bump_dashboard_cache_version():
    _bump_cache_version(settings.DASHBOARD_CACHE_VERSION_KEY)


def bump_export_cache_version():
    _bump_cache_version(settings.EXPORT_CACHE_VERSION_KEY)


def _normalize_value(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return str(value)
    return str(value)

def _get_actor_display(user):
    if user and getattr(user, "is_authenticated", False):
        full_name = user.get_full_name().strip() if hasattr(user, "get_full_name") else ""
        return full_name or user.get_username()
    return "Система"

@receiver(pre_save, sender=DailyProduction)
def collect_daily_production_changes(sender, instance, **kwargs):
    instance._audit_changes = []
    instance._audit_user = get_current_user()

    # Если это новый объект, сравнивать пока не с чем
    if instance._state.adding or not instance.pk:
        return

    try:
        old_instance = DailyProduction.objects.select_related("well").get(pk=instance.pk)
    except DailyProduction.DoesNotExist:
        return

    for field_name in AUDITED_FIELDS:
        old_value = getattr(old_instance, field_name, None)
        new_value = getattr(instance, field_name, None)

        if old_value != new_value:
            instance._audit_changes.append(
                {
                    "field_name": field_name,
                    "field_verbose_name": AUDITED_FIELD_LABELS.get(field_name, field_name),
                    "old_value": _normalize_value(old_value),
                    "new_value": _normalize_value(new_value),
                    "old_raw": old_value,
                    "new_raw": new_value,
                    "well": old_instance.well,
                    "date": old_instance.date,
                }
            )

@receiver(post_save, sender=DailyProduction)
def create_daily_production_audit_logs(sender, instance, created, **kwargs):
    user = getattr(instance, "_audit_user", None)
    if user is None:
        user = get_current_user()

    actor_display = _get_actor_display(user)

    well_obj = instance.well
    well_name = well_obj.name if well_obj else ""
    report_date = instance.date

    # 1. Логирование создания нового рапорта
    if created:
        message = (
            f"Пользователь [{actor_display}] создал рапорт "
            f"по скважине [{well_name}] за дату [{report_date}]"
        )

        def _save_create_log():
            ProductionAuditLog.objects.create(
                daily_production=instance,
                well=well_obj,
                changed_by=user if getattr(user, "is_authenticated", False) else None,
                changed_by_username=actor_display,
                well_name_snapshot=well_name,
                report_date_snapshot=report_date,
                action=ProductionAuditLog.Action.CREATE,
                field_name="",
                field_verbose_name="",
                old_value="",
                new_value="",
                message=message,
            )

        transaction.on_commit(_save_create_log)
        return

    # 2. Логирование обновления существующего рапорта
    changes = getattr(instance, "_audit_changes", None) or []
    if not changes:
        return

    logs = []
    for change in changes:
        field_name = change["field_name"]
        field_verbose_name = change["field_verbose_name"]
        old_value = change["old_value"] or ""
        new_value = change["new_value"] or ""

        message = (
            f"Пользователь [{actor_display}] изменил поле "
            f"[{field_name}] у скважины [{well_name}] "
            f"с [{old_value}] на [{new_value}]"
        )

        logs.append(
            ProductionAuditLog(
                daily_production=instance,
                well=well_obj,
                changed_by=user if getattr(user, "is_authenticated", False) else None,
                changed_by_username=actor_display,
                well_name_snapshot=well_name,
                report_date_snapshot=report_date,
                action=ProductionAuditLog.Action.UPDATE,
                field_name=field_name,
                field_verbose_name=field_verbose_name,
                old_value=old_value,
                new_value=new_value,
                message=message,
            )
        )

    def _save_update_logs():
        ProductionAuditLog.objects.bulk_create(logs)

    transaction.on_commit(_save_update_logs)


@receiver(post_save, sender=DailyProduction)
@receiver(post_delete, sender=DailyProduction)
@receiver(post_save, sender=Well)
@receiver(post_delete, sender=Well)
@receiver(post_save, sender=OilCompany)
@receiver(post_delete, sender=OilCompany)
@receiver(post_save, sender=Profile)
@receiver(post_delete, sender=Profile)
def invalidate_analytics_caches(*args, **kwargs):
    bump_dashboard_cache_version()
    bump_export_cache_version()