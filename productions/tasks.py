import hashlib
import json

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.db import transaction

from notifications.models import Notification
from notifications.services import create_notification
from .models import DailyProductionImportJob, MonthlyProductionExportJob
from .services.excel_export import build_monthly_production_report
from .services.excel_import import process_daily_productions_excel


def _get_export_cache_version():
    try:
        version = cache.get(settings.EXPORT_CACHE_VERSION_KEY)
        if version is None:
            cache.set(settings.EXPORT_CACHE_VERSION_KEY, 1, None)
            return 1
        return version
    except Exception:
        return 1


def _build_export_cache_key(year: int, month: int):
    payload = json.dumps(
        {
            "year": year,
            "month": month,
            "version": _get_export_cache_version(),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    digest = hashlib.md5(payload.encode("utf-8")).hexdigest()
    return f"export:monthly:{digest}"


def _send_import_result_email(job: DailyProductionImportJob):
    user = job.uploaded_by
    if not user.email:
        return

    filename = job.original_filename or "Excel-файл"

    if job.status == DailyProductionImportJob.Status.SUCCESS:
        subject = "Импорт суточных рапортов завершён успешно"
        message = (
            f"Здравствуйте!\n\n"
            f"Импорт файла '{filename}' успешно завершён.\n\n"
            f"ID импорта: {job.id}\n"
            f"Создано записей: {job.created_count}\n"
            f"Пропущено строк: {job.skipped_count}\n"
            f"Ошибок: {job.error_count}\n"
        )

    elif job.status == DailyProductionImportJob.Status.COMPLETED_WITH_ERRORS:
        preview = "\n".join(f"- {err}" for err in job.errors_preview[:10])
        subject = "Импорт суточных рапортов завершён с ошибками"
        message = (
            f"Здравствуйте!\n\n"
            f"Импорт файла '{filename}' завершён, но есть ошибки.\n\n"
            f"ID импорта: {job.id}\n"
            f"Создано записей: {job.created_count}\n"
            f"Пропущено строк: {job.skipped_count}\n"
            f"Ошибок: {job.error_count}\n\n"
            f"Первые ошибки:\n{preview if preview else 'Нет деталей'}\n"
        )

    else:
        subject = "Ошибка фонового импорта суточных рапортов"
        message = (
            f"Здравствуйте!\n\n"
            f"При обработке файла '{filename}' произошла ошибка.\n\n"
            f"ID импорта: {job.id}\n"
            f"Ошибка: {job.fatal_error or 'Неизвестная ошибка'}\n"
        )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def _create_import_notification(job: DailyProductionImportJob):
    filename = job.original_filename or "Excel-файл"

    if job.status == DailyProductionImportJob.Status.SUCCESS:
        create_notification(
            recipient=job.uploaded_by,
            title="Импорт завершён успешно",
            message=(
                f"Файл '{filename}' успешно обработан. "
                f"Создано записей: {job.created_count}."
            ),
            level=Notification.Level.SUCCESS,
            related_import=job,
        )

    elif job.status == DailyProductionImportJob.Status.COMPLETED_WITH_ERRORS:
        create_notification(
            recipient=job.uploaded_by,
            title="Импорт завершён с ошибками",
            message=(
                f"Файл '{filename}' обработан, но есть ошибки. "
                f"Создано записей: {job.created_count}, ошибок: {job.error_count}."
            ),
            level=Notification.Level.WARNING,
            related_import=job,
        )

    else:
        create_notification(
            recipient=job.uploaded_by,
            title="Ошибка фонового импорта",
            message=(
                f"Файл '{filename}' не удалось обработать. "
                f"Причина: {job.fatal_error or 'Неизвестная ошибка'}"
            ),
            level=Notification.Level.ERROR,
            related_import=job,
        )


def _send_export_result_email(job: MonthlyProductionExportJob):
    user = job.requested_by
    if not user.email:
        return

    if job.status == MonthlyProductionExportJob.Status.SUCCESS:
        source_label = "из кэша" if job.reused_cache else "заново"
        subject = "Месячный отчёт готов"
        message = (
            f"Здравствуйте!\n\n"
            f"Месячный отчёт за {job.period_label} готов.\n\n"
            f"ID экспорта: {job.id}\n"
            f"Файл подготовлен: {source_label}\n"
            f"Скачайте его в разделе уведомлений или через страницу системы.\n"
        )
    else:
        subject = "Ошибка подготовки месячного отчёта"
        message = (
            f"Здравствуйте!\n\n"
            f"Не удалось подготовить месячный отчёт за {job.period_label}.\n\n"
            f"ID экспорта: {job.id}\n"
            f"Ошибка: {job.fatal_error or 'Неизвестная ошибка'}\n"
        )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def _create_export_notification(job: MonthlyProductionExportJob):
    if job.status == MonthlyProductionExportJob.Status.SUCCESS:
        source_label = "из кэша" if job.reused_cache else "новый файл"
        create_notification(
            recipient=job.requested_by,
            title="Месячный отчёт готов",
            message=(
                f"Отчёт за {job.period_label} подготовлен. "
                f"Источник: {source_label}. Нажмите скачать в уведомлении."
            ),
            level=Notification.Level.SUCCESS,
            related_export=job,
        )
    else:
        create_notification(
            recipient=job.requested_by,
            title="Ошибка подготовки месячного отчёта",
            message=(
                f"Не удалось подготовить отчёт за {job.period_label}. "
                f"Причина: {job.fatal_error or 'Неизвестная ошибка'}"
            ),
            level=Notification.Level.ERROR,
            related_export=job,
        )


@shared_task(bind=True)
def import_daily_productions(self, import_job_id: int):
    job = DailyProductionImportJob.objects.get(pk=import_job_id)
    job.mark_processing(task_id=self.request.id)

    try:
        result = process_daily_productions_excel(job.file.path)

        with transaction.atomic():
            job.mark_success(
                created_count=result["created_count"],
                skipped_count=result["skipped_count"],
                errors_preview=result["errors"],
            )

        job.refresh_from_db()
        _create_import_notification(job)
        _send_import_result_email(job)

        return {
            "status": job.status,
            "created_count": result["created_count"],
            "skipped_count": result["skipped_count"],
            "error_count": len(result["errors"]),
        }

    except Exception as exc:
        job.mark_failed(str(exc))
        job.refresh_from_db()

        try:
            _create_import_notification(job)
        except Exception:
            pass

        try:
            _send_import_result_email(job)
        except Exception:
            pass

        raise


@shared_task(bind=True)
def generate_monthly_production_export(self, export_job_id: int):
    job = MonthlyProductionExportJob.objects.get(pk=export_job_id)
    job.mark_processing(task_id=self.request.id)

    try:
        cache_key = _build_export_cache_key(job.year, job.month)

        try:
            cached_file_name = cache.get(cache_key)
        except Exception:
            cached_file_name = None

        if cached_file_name and default_storage.exists(cached_file_name):
            job.file.name = cached_file_name
            job.mark_success(reused_cache=True)
            job.refresh_from_db()
            _create_export_notification(job)
            _send_export_result_email(job)

            return {
                "status": job.status,
                "cached": True,
                "file": job.file.name,
            }

        output = build_monthly_production_report(year=job.year, month=job.month)
        filename = f"monthly_production_report_{job.year}_{job.month:02d}.xlsx"

        job.file.save(filename, ContentFile(output.getvalue()), save=False)
        job.mark_success(reused_cache=False)

        try:
            cache.set(cache_key, job.file.name, settings.EXPORT_CACHE_TIMEOUT)
        except Exception:
            pass

        job.refresh_from_db()
        _create_export_notification(job)
        _send_export_result_email(job)

        return {
            "status": job.status,
            "cached": False,
            "file": job.file.name,
        }

    except Exception as exc:
        job.mark_failed(str(exc))
        job.refresh_from_db()

        try:
            _create_export_notification(job)
        except Exception:
            pass

        try:
            _send_export_result_email(job)
        except Exception:
            pass

        raise