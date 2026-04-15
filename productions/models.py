from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from companies.models import OilCompany


class Well(models.Model):
    name = models.CharField(
        "Название скважины",
        max_length=100,
        unique=True,
        error_messages={
            "unique": "Скважина с таким названием уже существует.",
            "blank": "Введите название скважины.",
        },
    )
    oil_company = models.ForeignKey(
        OilCompany,
        on_delete=models.CASCADE,
        related_name="wells",
        verbose_name="Нефтяная компания",
        error_messages={
            "blank": "Выберите нефтяную компанию.",
        },
    )
    type = models.CharField(
        "Тип",
        max_length=100,
        error_messages={
            "blank": "Укажите тип скважины.",
        },
    )
    max_drilling_depth = models.PositiveIntegerField(
        "Максимальная глубина бурения, м",
        error_messages={
            "invalid": "Введите корректную максимальную глубину бурения.",
        },
    )
    latitude = models.DecimalField(
        "Широта",
        max_digits=9,
        decimal_places=6,
        error_messages={
            "invalid": "Введите корректное значение широты.",
        },
    )
    longitude = models.DecimalField(
        "Долгота",
        max_digits=9,
        decimal_places=6,
        error_messages={
            "invalid": "Введите корректное значение долготы.",
        },
    )

    def __str__(self):
        return self.name


class DailyProduction(models.Model):
    well = models.ForeignKey(
        Well,
        on_delete=models.CASCADE,
        related_name="daily_productions",
        verbose_name="Скважина",
    )
    date = models.DateField(
        "Дата",
        error_messages={
            "blank": "Укажите дату.",
            "invalid": "Введите корректную дату.",
        },
    )
    work_time = models.DecimalField(
        "Время работы, часов",
        max_digits=4,
        decimal_places=2,
        validators=[
            MinValueValidator(0, message="Время работы не может быть меньше 0 часов."),
            MaxValueValidator(24, message="Время работы не может быть больше 24 часов."),
        ],
        error_messages={
            "blank": "Укажите время работы.",
            "invalid": "Введите корректное число часов.",
        },
    )
    liquid_debit = models.DecimalField(
        "Дебит жидкости, м³/сут",
        max_digits=10,
        decimal_places=2,
        error_messages={
            "blank": "Укажите дебит жидкости.",
            "invalid": "Введите корректное значение дебита жидкости.",
        },
    )
    water_cut = models.DecimalField(
        "Обводненность, %",
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(0, message="Обводненность не может быть меньше 0%."),
            MaxValueValidator(100, message="Обводненность не может быть больше 100%."),
        ],
        error_messages={
            "blank": "Укажите обводненность.",
            "invalid": "Введите корректное значение обводненности.",
        },
    )
    oil_density = models.DecimalField(
        "Плотность нефти, т/м³",
        max_digits=5,
        decimal_places=3,
        error_messages={
            "blank": "Укажите плотность нефти.",
            "invalid": "Введите корректное значение плотности нефти.",
        },
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["well", "date"],
                name="unique_daily_production_per_well_date",
                violation_error_message="Для этой скважины уже есть запись на указанную дату.",
            )
        ]
        verbose_name = "Суточный рапорт"
        verbose_name_plural = "Суточные рапорты"

    def __str__(self):
        return f"{self.well} - {self.date}"

    @property
    def calculated_oil(self):
        return self.liquid_debit * (Decimal("1") - self.water_cut / Decimal("100")) * self.oil_density


class ProductionAuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = "create", "Создание"
        UPDATE = "update", "Изменение"
        DELETE = "delete", "Удаление"

    daily_production = models.ForeignKey(
        DailyProduction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name="Суточный рапорт",
    )
    well = models.ForeignKey(
        Well,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name="Скважина",
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="production_audit_logs",
        verbose_name="Пользователь",
    )

    # Snapshot-поля, чтобы история не терялась даже если связанные объекты потом изменятся/удалятся
    changed_by_username = models.CharField(
        "Имя пользователя (снимок)",
        max_length=150,
        blank=True,
    )
    well_name_snapshot = models.CharField(
        "Название скважины (снимок)",
        max_length=100,
        blank=True,
    )
    report_date_snapshot = models.DateField(
        "Дата рапорта (снимок)",
        null=True,
        blank=True,
    )

    action = models.CharField(
        "Тип действия",
        max_length=20,
        choices=Action.choices,
        default=Action.UPDATE,
    )
    field_name = models.CharField(
        "Техническое имя поля",
        max_length=100,
        blank=True,
    )
    field_verbose_name = models.CharField(
        "Название поля",
        max_length=255,
        blank=True,
    )
    old_value = models.TextField(
        "Старое значение",
        blank=True,
    )
    new_value = models.TextField(
        "Новое значение",
        blank=True,
    )
    message = models.TextField(
        "Текст лога",
        blank=True,
    )
    changed_at = models.DateTimeField(
        "Дата и время изменения",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Журнал аудита рапортов"
        verbose_name_plural = "Журнал аудита рапортов"
        ordering = ["-changed_at"]
        indexes = [
            models.Index(fields=["-changed_at"]),
            models.Index(fields=["action"]),
            models.Index(fields=["field_name"]),
        ]

    def __str__(self):
        field_part = f" / {self.field_name}" if self.field_name else ""
        well_part = self.well_name_snapshot or (self.well.name if self.well else "—")
        return f"{self.get_action_display()}{field_part} / {well_part} / {self.changed_at:%Y-%m-%d %H:%M}"

class DailyProductionImportJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает"
        PROCESSING = "processing", "Обрабатывается"
        SUCCESS = "success", "Успешно"
        COMPLETED_WITH_ERRORS = "completed_with_errors", "Завершено с ошибками"
        FAILED = "failed", "Ошибка"

    file = models.FileField(
        "Excel-файл",
        upload_to="imports/daily_productions/%Y/%m/%d/",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_production_import_jobs",
        verbose_name="Загрузил",
    )
    status = models.CharField(
        "Статус",
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
    )
    celery_task_id = models.CharField(
        "ID Celery-задачи",
        max_length=255,
        blank=True,
    )

    created_count = models.PositiveIntegerField("Создано записей", default=0)
    skipped_count = models.PositiveIntegerField("Пропущено строк", default=0)
    error_count = models.PositiveIntegerField("Количество ошибок", default=0)

    errors_preview = models.JSONField(
        "Ошибки (превью)",
        default=list,
        blank=True,
    )
    fatal_error = models.TextField(
        "Критическая ошибка",
        blank=True,
    )

    uploaded_at = models.DateTimeField("Загружено", auto_now_add=True)
    started_at = models.DateTimeField("Начато", blank=True, null=True)
    finished_at = models.DateTimeField("Завершено", blank=True, null=True)

    class Meta:
        verbose_name = "Задача импорта суточных рапортов"
        verbose_name_plural = "Задачи импорта суточных рапортов"
        ordering = ["-uploaded_at"]

    def mark_processing(self, task_id: str = ""):
        self.status = self.Status.PROCESSING
        self.started_at = timezone.now()
        if task_id:
            self.celery_task_id = task_id
        self.save(update_fields=["status", "started_at", "celery_task_id"])

    def mark_success(self, created_count: int, skipped_count: int, errors_preview: list[str]):
        self.created_count = created_count
        self.skipped_count = skipped_count
        self.error_count = len(errors_preview)
        self.errors_preview = errors_preview[:50]
        self.status = (
            self.Status.COMPLETED_WITH_ERRORS if errors_preview else self.Status.SUCCESS
        )
        self.finished_at = timezone.now()
        self.save(
            update_fields=[
                "created_count",
                "skipped_count",
                "error_count",
                "errors_preview",
                "status",
                "finished_at",
            ]
        )

    def mark_failed(self, message: str):
        self.status = self.Status.FAILED
        self.fatal_error = message
        self.finished_at = timezone.now()
        self.save(update_fields=["status", "fatal_error", "finished_at"])

    @property
    def original_filename(self):
        if not self.file:
            return ""
        return self.file.name.split("/")[-1]

    def __str__(self):
        return f"Импорт #{self.pk} — {self.get_status_display()}"


class MonthlyProductionExportJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает"
        PROCESSING = "processing", "Обрабатывается"
        SUCCESS = "success", "Успешно"
        FAILED = "failed", "Ошибка"

    year = models.PositiveIntegerField("Год")
    month = models.PositiveSmallIntegerField("Месяц")
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="monthly_export_jobs",
        verbose_name="Запросил",
    )
    status = models.CharField(
        "Статус",
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
    )
    celery_task_id = models.CharField(
        "ID Celery-задачи",
        max_length=255,
        blank=True,
    )
    file = models.FileField(
        "Готовый файл",
        upload_to="exports/monthly/%Y/%m/",
        blank=True,
    )
    reused_cache = models.BooleanField("Использован кэш", default=False)
    fatal_error = models.TextField("Ошибка", blank=True)

    created_at = models.DateTimeField("Создано", auto_now_add=True)
    started_at = models.DateTimeField("Начато", blank=True, null=True)
    finished_at = models.DateTimeField("Завершено", blank=True, null=True)

    class Meta:
        verbose_name = "Задача экспорта месячного отчёта"
        verbose_name_plural = "Задачи экспорта месячных отчётов"
        ordering = ["-created_at"]

    def mark_processing(self, task_id: str = ""):
        self.status = self.Status.PROCESSING
        self.started_at = timezone.now()
        if task_id:
            self.celery_task_id = task_id
        self.save(update_fields=["status", "started_at", "celery_task_id"])

    def mark_success(self, reused_cache: bool = False):
        self.status = self.Status.SUCCESS
        self.reused_cache = reused_cache
        self.finished_at = timezone.now()
        self.save(update_fields=["file", "status", "reused_cache", "finished_at"])

    def mark_failed(self, message: str):
        self.status = self.Status.FAILED
        self.fatal_error = message
        self.finished_at = timezone.now()
        self.save(update_fields=["status", "fatal_error", "finished_at"])

    @property
    def original_filename(self):
        if not self.file:
            return ""
        return self.file.name.split("/")[-1]

    @property
    def period_label(self):
        return f"{self.month:02d}.{self.year}"

    def __str__(self):
        return f"Экспорт #{self.pk} — {self.period_label}"