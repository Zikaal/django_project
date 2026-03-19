from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


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