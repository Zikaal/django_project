from celery import shared_task
from django.db import transaction

from .models import DailyProductionImportJob
from .services.excel_import import process_daily_productions_excel


@shared_task(bind=True)
def import_daily_productions(self, import_job_id: int):
    """
    Фоновая задача импорта Excel-файла с суточными рапортами.
    На вход получает не request и не uploaded file, а ID сохранённой записи импорта.
    """
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

        return {
            "status": job.status,
            "created_count": result["created_count"],
            "skipped_count": result["skipped_count"],
            "error_count": len(result["errors"]),
        }

    except Exception as exc:
        job.mark_failed(str(exc))
        raise