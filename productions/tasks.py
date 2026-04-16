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

from productions.signals import bump_dashboard_cache_version, bump_export_cache_version


def _get_export_cache_version():
    """
    Возвращает текущую версию кэша экспортов.

    Идея:
    - экспортные файлы кэшируются не просто по месяцу и году,
      а по месяцу/году + версии данных;
    - когда данные меняются, версия увеличивается;
    - старые cache keys автоматически становятся неактуальными.

    Если кэш временно недоступен:
    - возвращаем безопасное значение 1.
    """
    try:
        version = cache.get(settings.EXPORT_CACHE_VERSION_KEY)
        if version is None:
            cache.set(settings.EXPORT_CACHE_VERSION_KEY, 1, None)
            return 1
        return version
    except Exception:
        return 1


def _build_export_cache_key(year: int, month: int):
    """
    Строит стабильный cache key для готового месячного экспорта.

    В ключ включаются:
    - год;
    - месяц;
    - текущая версия export-кэша.

    Затем payload хэшируется в md5,
    чтобы key был коротким и стабильным.
    """
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
    """
    Отправляет email пользователю по результату импорта.

    Сценарии:
    - SUCCESS: импорт завершился без ошибок;
    - COMPLETED_WITH_ERRORS: импорт завершился, но часть строк с ошибками;
    - FAILED: импорт полностью завершился ошибкой.

    Если у пользователя нет email:
    - просто ничего не делаем.
    """
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
    """
    Создает внутреннее уведомление пользователю по результату импорта.

    Логика аналогична email:
    - success -> SUCCESS notification;
    - completed_with_errors -> WARNING notification;
    - failed -> ERROR notification.
    """
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
    """
    Отправляет email по результату месячного экспорта.

    Если экспорт успешен:
    - сообщаем, что файл готов;
    - отдельно указываем, был ли он взят из кэша или собран заново.

    Если экспорт завершился ошибкой:
    - отправляем текст ошибки.
    """
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
    """
    Создает внутреннее уведомление пользователю по результату экспорта.
    """
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
    """
    Celery-задача фонового импорта Excel-файла с суточными рапортами.

    Алгоритм:
    1. Получаем объект DailyProductionImportJob.
    2. Переводим его в статус processing и сохраняем Celery task id.
    3. Запускаем парсинг и обработку Excel.
    4. Обновляем итоговый статус и счетчики.
    5. Инвалидируем dashboard/export cache, потому что данные изменились.
    6. Создаем уведомление и отправляем email.
    7. Возвращаем краткий JSON-результат задачи.

    При любой ошибке:
    - job помечается как failed;
    - пользователю все равно пытаемся отправить уведомление и email;
    - исключение пробрасывается дальше, чтобы Celery его зафиксировал.
    """
    job = DailyProductionImportJob.objects.get(pk=import_job_id)
    job.mark_processing(task_id=self.request.id)

    try:
        result = process_daily_productions_excel(job.file.path)

        # Обновление итогов импорта делаем внутри транзакции.
        with transaction.atomic():
            job.mark_success(
                created_count=result["created_count"],
                skipped_count=result["skipped_count"],
                errors_preview=result["errors"],
            )

        # После успешного импорта аналитика и экспортные файлы
        # могут стать неактуальными, поэтому повышаем версии кэша.
        bump_dashboard_cache_version()
        bump_export_cache_version()

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

        # Побочные действия оборачиваем в try/except,
        # чтобы вторичная ошибка не скрыла исходную причину падения задачи.
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
    """
    Celery-задача генерации месячного Excel-отчета.

    Алгоритм:
    1. Получаем объект MonthlyProductionExportJob.
    2. Переводим его в processing.
    3. Пытаемся найти уже готовый файл в кэше.
    4. Если файл есть — переиспользуем его.
    5. Если файла нет — строим новый Excel через build_monthly_production_report().
    6. Сохраняем файл в storage.
    7. Обновляем статус job и кладем имя файла в кэш.
    8. Создаем уведомление и шлем email.

    При ошибке:
    - job помечается как failed;
    - пользователю отправляется уведомление/письмо;
    - исключение пробрасывается дальше в Celery.
    """
    job = MonthlyProductionExportJob.objects.get(pk=export_job_id)
    job.mark_processing(task_id=self.request.id)

    try:
        cache_key = _build_export_cache_key(job.year, job.month)

        try:
            cached_file_name = cache.get(cache_key)
        except Exception:
            cached_file_name = None

        # Если файл уже есть в кэше и физически существует в storage,
        # можно не пересобирать отчет заново.
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

        # Генерируем отчет заново.
        output = build_monthly_production_report(year=job.year, month=job.month)
        filename = f"monthly_production_report_{job.year}_{job.month:02d}.xlsx"

        # save=False здесь важен:
        # сначала присваиваем файл, а статус и прочие поля обновляются через mark_success().
        job.file.save(filename, ContentFile(output.getvalue()), save=False)
        job.mark_success(reused_cache=False)

        # Сохраняем имя файла в кэш для повторного использования.
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