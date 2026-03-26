from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from companies.models import OilCompany


class Well(models.Model):
    """
    Модель скважины (Well).

    Хранит основную информацию о нефтяной скважине, включая её местоположение,
    принадлежность к компании и технические характеристики.
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
        """Строковое представление скважины — возвращает её название."""
        return self.name


class DailyProduction(models.Model):
    """
    Модель суточного рапорта по добыче (DailyProduction).

    Хранит ежедневные показатели добычи по каждой скважине.
    Обеспечивает уникальность записи для комбинации "скважина + дата".
    """

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
        """
        Метаданные модели:
        - Уникальное ограничение: одна запись на скважину в сутки
        - Человеко-читаемые названия в админке и формах
        """
        constraints = [
            models.UniqueConstraint(
                fields=["well", "date"],
                name="unique_daily_production_per_well_date",
                violation_error_message="Для этой скважины уже есть запись на указанную дату.",
            )
        ]
        verbose_name = "Суточный рапорт"
        verbose_name_plural = "Суточные рапорты"
        # Можно добавить ordering = ['-date'] при необходимости

    def __str__(self):
        """Строковое представление суточного рапорта."""
        return f"{self.well} - {self.date}"

    @property
    def calculated_oil(self):
        """
        Расчётное количество добытой нефти за сутки (в тоннах).

        Формула:
            Объём нефти (м³) = Дебит жидкости × (1 - Обводнённость/100)
            Масса нефти (т)   = Объём нефти × Плотность нефти

        Возвращает:
            Decimal — масса добытой нефти в тоннах.
        """
        return self.liquid_debit * (Decimal("1") - self.water_cut / Decimal("100")) * self.oil_density