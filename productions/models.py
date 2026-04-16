from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from companies.models import OilCompany


class Well(models.Model):
    """
    Модель скважины.

    Для чего нужна:
    - хранит базовую информацию о скважине;
    - связывает производственные рапорты с конкретной компанией;
    - используется в справочниках, фильтрах, отчетах и dashboard.

    Связи:
    - каждая скважина принадлежит одной нефтяной компании;
    - у одной компании может быть много скважин.
    """

    name = models.CharField(
        "Название скважины",
        max_length=100,
        unique=True,
        error_messages={
            "unique": "Скважина с таким названием уже существует.",
            "blank": "Введите название скважины.",
        },
    )
    # Уникальное имя скважины.
    # unique=True защищает от дублирования справочника скважин.

    oil_company = models.ForeignKey(
        OilCompany,
        on_delete=models.CASCADE,
        related_name="wells",
        verbose_name="Нефтяная компания",
        error_messages={
            "blank": "Выберите нефтяную компанию.",
        },
    )
    # Компания, к которой относится скважина.
    #
    # related_name="wells" позволяет писать:
    #   company.wells.all()
    #
    # on_delete=models.CASCADE означает:
    # если удалить компанию, связанные скважины тоже удалятся.

    type = models.CharField(
        "Тип",
        max_length=100,
        error_messages={
            "blank": "Укажите тип скважины.",
        },
    )
    # Тип скважины, например:
    # - добывающая
    # - нагнетательная
    # - разведочная

    max_drilling_depth = models.PositiveIntegerField(
        "Максимальная глубина бурения, м",
        error_messages={
            "invalid": "Введите корректную максимальную глубину бурения.",
        },
    )
    # Максимальная глубина бурения в метрах.

    latitude = models.DecimalField(
        "Широта",
        max_digits=9,
        decimal_places=6,
        error_messages={
            "invalid": "Введите корректное значение широты.",
        },
    )
    # Географическая широта скважины.

    longitude = models.DecimalField(
        "Долгота",
        max_digits=9,
        decimal_places=6,
        error_messages={
            "invalid": "Введите корректное значение долготы.",
        },
    )
    # Географическая долгота скважины.

    def __str__(self):
        """
        Человекочитаемое строковое представление скважины.
        """
        return self.name


class DailyProduction(models.Model):
    """
    Суточный производственный рапорт по скважине.

    Что хранит:
    - дату;
    - время работы;
    - дебит жидкости;
    - обводненность;
    - плотность нефти.

    Ключевое бизнес-правило:
    - для одной и той же скважины может существовать только один рапорт на одну дату.
    """

    well = models.ForeignKey(
        Well,
        on_delete=models.CASCADE,
        related_name="daily_productions",
        verbose_name="Скважина",
    )
    # Скважина, к которой относится рапорт.
    #
    # related_name="daily_productions" позволяет писать:
    #   well.daily_productions.all()

    date = models.DateField(
        "Дата",
        error_messages={
            "blank": "Укажите дату.",
            "invalid": "Введите корректную дату.",
        },
    )
    # Дата, за которую заполняется рапорт.

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
    # Количество часов работы за сутки.
    # Ограничено диапазоном 0..24.

    liquid_debit = models.DecimalField(
        "Дебит жидкости, м³/сут",
        max_digits=10,
        decimal_places=2,
        error_messages={
            "blank": "Укажите дебит жидкости.",
            "invalid": "Введите корректное значение дебита жидкости.",
        },
    )
    # Общий дебит жидкости за сутки.

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
    # Процент воды в продукции.
    # Ограничен диапазоном 0..100.

    oil_density = models.DecimalField(
        "Плотность нефти, т/м³",
        max_digits=5,
        decimal_places=3,
        error_messages={
            "blank": "Укажите плотность нефти.",
            "invalid": "Введите корректное значение плотности нефти.",
        },
    )
    # Плотность нефти в т/м³.

    class Meta:
        """
        Метаданные модели DailyProduction.
        """

        constraints = [
            models.UniqueConstraint(
                fields=["well", "date"],
                name="unique_daily_production_per_well_date",
                violation_error_message="Для этой скважины уже есть запись на указанную дату.",
            )
        ]
        # Защита на уровне БД:
        # у одной скважины не может быть двух рапортов на одну дату.

        verbose_name = "Суточный рапорт"
        verbose_name_plural = "Суточные рапорты"

    def __str__(self):
        """
        Строковое представление рапорта.
        """
        return f"{self.well} - {self.date}"

    @property
    def calculated_oil(self):
        """
        Вычисляемый показатель чистой нефти.

        Формула:
            liquid_debit * (1 - water_cut / 100) * oil_density

        Почему property:
        - значение можно быстро получить в коде, шаблонах и admin;
        - его не нужно хранить отдельным полем в БД.
        """
        return self.liquid_debit * (Decimal("1") - self.water_cut / Decimal("100")) * self.oil_density


class ProductionAuditLog(models.Model):
    """
    Журнал аудита изменений суточных рапортов.

    Для чего нужен:
    - фиксирует создание и изменение рапортов;
    - показывает, кто и что поменял;
    - хранит snapshot-данные, чтобы история не терялась со временем.
    """

    class Action(models.TextChoices):
        """
        Поддерживаемые типы действий в журнале аудита.
        """

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
    # Ссылка на исходный рапорт.
    # SET_NULL выбран правильно:
    # даже если сам рапорт удалят, лог должен остаться.

    well = models.ForeignKey(
        Well,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name="Скважина",
    )
    # Ссылка на скважину.
    # Тоже SET_NULL, чтобы история не пропала при удалении объекта.

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="production_audit_logs",
        verbose_name="Пользователь",
    )
    # Пользователь, который инициировал изменение.
    # Если пользователя удалят, лог должен сохраниться, поэтому SET_NULL.

    # Snapshot-поля:
    # сохраняют человекочитаемое состояние на момент события,
    # даже если связанные объекты потом изменились или были удалены.
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
    # Тип события аудита: create / update / delete.

    field_name = models.CharField(
        "Техническое имя поля",
        max_length=100,
        blank=True,
    )
    # Внутреннее имя поля, например: water_cut.

    field_verbose_name = models.CharField(
        "Название поля",
        max_length=255,
        blank=True,
    )
    # Человекочитаемое название поля для UI и журналов.

    old_value = models.TextField(
        "Старое значение",
        blank=True,
    )
    # Предыдущее значение поля.

    new_value = models.TextField(
        "Новое значение",
        blank=True,
    )
    # Новое значение поля.

    message = models.TextField(
        "Текст лога",
        blank=True,
    )
    # Полностью сформированное текстовое сообщение аудита.

    changed_at = models.DateTimeField(
        "Дата и время изменения",
        auto_now_add=True,
    )
    # Когда произошло изменение.

    class Meta:
        """
        Метаданные модели журнала аудита.
        """

        verbose_name = "Журнал аудита рапортов"
        verbose_name_plural = "Журнал аудита рапортов"
        ordering = ["-changed_at"]
        indexes = [
            models.Index(fields=["-changed_at"]),
            models.Index(fields=["action"]),
            models.Index(fields=["field_name"]),
        ]
        # Индексы полезны для:
        # - быстрого поиска последних событий;
        # - фильтрации по action;
        # - поиска изменений по конкретному полю.

    def __str__(self):
        """
        Строковое представление аудита для admin/shell.
        """
        field_part = f" / {self.field_name}" if self.field_name else ""
        well_part = self.well_name_snapshot or (self.well.name if self.well else "—")
        return f"{self.get_action_display()}{field_part} / {well_part} / {self.changed_at:%Y-%m-%d %H:%M}"


class DailyProductionImportJob(models.Model):
    """
    Модель фоновой задачи импорта Excel-файла с суточными рапортами.

    Идея:
    - пользователь загружает файл;
    - создается ImportJob со статусом pending;
    - Celery обрабатывает файл в фоне;
    - job хранит итог, счетчики и превью ошибок.
    """

    class Status(models.TextChoices):
        """
        Возможные статусы задачи импорта.
        """

        PENDING = "pending", "Ожидает"
        PROCESSING = "processing", "Обрабатывается"
        SUCCESS = "success", "Успешно"
        COMPLETED_WITH_ERRORS = "completed_with_errors", "Завершено с ошибками"
        FAILED = "failed", "Ошибка"

    file = models.FileField(
        "Excel-файл",
        upload_to="imports/daily_productions/%Y/%m/%d/",
    )
    # Загруженный пользователем Excel-файл.

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_production_import_jobs",
        verbose_name="Загрузил",
    )
    # Пользователь, который загрузил файл.

    status = models.CharField(
        "Статус",
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
    )
    # Текущий статус job.

    celery_task_id = models.CharField(
        "ID Celery-задачи",
        max_length=255,
        blank=True,
    )
    # Идентификатор задачи в Celery для трассировки и отладки.

    created_count = models.PositiveIntegerField("Создано записей", default=0)
    skipped_count = models.PositiveIntegerField("Пропущено строк", default=0)
    error_count = models.PositiveIntegerField("Количество ошибок", default=0)
    # Сводные счетчики по результату импорта.

    errors_preview = models.JSONField(
        "Ошибки (превью)",
        default=list,
        blank=True,
    )
    # Небольшой список первых ошибок, чтобы их удобно было показывать в UI.

    fatal_error = models.TextField(
        "Критическая ошибка",
        blank=True,
    )
    # Текст фатальной ошибки, если задача упала полностью.

    uploaded_at = models.DateTimeField("Загружено", auto_now_add=True)
    started_at = models.DateTimeField("Начато", blank=True, null=True)
    finished_at = models.DateTimeField("Завершено", blank=True, null=True)
    # Временные метки жизненного цикла задачи.

    class Meta:
        """
        Метаданные задачи импорта.
        """

        verbose_name = "Задача импорта суточных рапортов"
        verbose_name_plural = "Задачи импорта суточных рапортов"
        ordering = ["-uploaded_at"]

    def mark_processing(self, task_id: str = ""):
        """
        Переводит job в статус processing.

        Дополнительно:
        - записывает started_at;
        - при наличии сохраняет celery task id.
        """
        self.status = self.Status.PROCESSING
        self.started_at = timezone.now()
        if task_id:
            self.celery_task_id = task_id
        self.save(update_fields=["status", "started_at", "celery_task_id"])

    def mark_success(self, created_count: int, skipped_count: int, errors_preview: list[str]):
        """
        Завершает job успешно или успешно с ошибками.

        Логика:
        - если errors_preview пустой -> SUCCESS;
        - если есть ошибки -> COMPLETED_WITH_ERRORS.
        """
        self.created_count = created_count
        self.skipped_count = skipped_count
        self.error_count = len(errors_preview)

        # Храним только ограниченное превью ошибок, чтобы JSON не разрастался бесконечно.
        self.errors_preview = errors_preview[:50]

        self.status = self.Status.COMPLETED_WITH_ERRORS if errors_preview else self.Status.SUCCESS
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
        """
        Переводит job в статус failed и сохраняет текст ошибки.
        """
        self.status = self.Status.FAILED
        self.fatal_error = message
        self.finished_at = timezone.now()
        self.save(update_fields=["status", "fatal_error", "finished_at"])

    @property
    def original_filename(self):
        """
        Возвращает имя файла без полного пути в storage.
        """
        if not self.file:
            return ""
        return self.file.name.split("/")[-1]

    def __str__(self):
        """
        Строковое представление job импорта.
        """
        return f"Импорт #{self.pk} — {self.get_status_display()}"


class MonthlyProductionExportJob(models.Model):
    """
    Модель фоновой задачи экспорта месячного отчета.

    Идея:
    - пользователь запрашивает экспорт за месяц;
    - создается ExportJob;
    - Celery генерирует файл в фоне или переиспользует кэш;
    - job хранит статус, файл и информацию о том, был ли использован кэш.
    """

    class Status(models.TextChoices):
        """
        Возможные статусы задачи экспорта.
        """

        PENDING = "pending", "Ожидает"
        PROCESSING = "processing", "Обрабатывается"
        SUCCESS = "success", "Успешно"
        FAILED = "failed", "Ошибка"

    year = models.PositiveIntegerField("Год")
    # Год экспорта.

    month = models.PositiveSmallIntegerField("Месяц")
    # Месяц экспорта.

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="monthly_export_jobs",
        verbose_name="Запросил",
    )
    # Пользователь, запросивший экспорт.

    status = models.CharField(
        "Статус",
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
    )
    # Текущий статус job.

    celery_task_id = models.CharField(
        "ID Celery-задачи",
        max_length=255,
        blank=True,
    )
    # Идентификатор фоновой Celery-задачи.

    file = models.FileField(
        "Готовый файл",
        upload_to="exports/monthly/%Y/%m/",
        blank=True,
    )
    # Готовый Excel-файл экспорта.

    reused_cache = models.BooleanField("Использован кэш", default=False)
    # Показывает, был ли файл взят из уже готового кэша, а не сгенерирован заново.

    fatal_error = models.TextField("Ошибка", blank=True)
    # Текст фатальной ошибки при неудачном экспорте.

    created_at = models.DateTimeField("Создано", auto_now_add=True)
    started_at = models.DateTimeField("Начато", blank=True, null=True)
    finished_at = models.DateTimeField("Завершено", blank=True, null=True)
    # Временные метки жизненного цикла задачи.

    class Meta:
        """
        Метаданные задачи экспорта.
        """

        verbose_name = "Задача экспорта месячного отчёта"
        verbose_name_plural = "Задачи экспорта месячных отчётов"
        ordering = ["-created_at"]

    def mark_processing(self, task_id: str = ""):
        """
        Переводит export job в статус processing.
        """
        self.status = self.Status.PROCESSING
        self.started_at = timezone.now()
        if task_id:
            self.celery_task_id = task_id
        self.save(update_fields=["status", "started_at", "celery_task_id"])

    def mark_success(self, reused_cache: bool = False):
        """
        Завершает export job успешно.

        Дополнительно:
        - сохраняет флаг reused_cache;
        - ставит finished_at.
        """
        self.status = self.Status.SUCCESS
        self.reused_cache = reused_cache
        self.finished_at = timezone.now()
        self.save(update_fields=["file", "status", "reused_cache", "finished_at"])

    def mark_failed(self, message: str):
        """
        Завершает export job ошибкой.
        """
        self.status = self.Status.FAILED
        self.fatal_error = message
        self.finished_at = timezone.now()
        self.save(update_fields=["status", "fatal_error", "finished_at"])

    @property
    def original_filename(self):
        """
        Возвращает имя готового файла без полного пути.
        """
        if not self.file:
            return ""
        return self.file.name.split("/")[-1]

    @property
    def period_label(self):
        """
        Удобное строковое представление периода в формате MM.YYYY.
        """
        return f"{self.month:02d}.{self.year}"

    def __str__(self):
        """
        Строковое представление export job.
        """
        return f"Экспорт #{self.pk} — {self.period_label}"
