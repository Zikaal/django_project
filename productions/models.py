from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Well(models.Model):  # Создаем модель Well для хранения информации о скважинах
    name = models.CharField("Название скважины", max_length=100, unique=True)  # Поле для названия скважины, максимум 100 символов, значение должно быть уникальным

    def __str__(self):  # Метод для удобного строкового отображения объекта
        return self.name  # Возвращаем название скважины


class DailyProduction(models.Model):  # Создаем модель DailyProduction для хранения суточных рапортов по добыче
    well = models.ForeignKey(  # Создаем внешний ключ на модель Well
        Well,  # Указываем, что связь идет с моделью Well
        on_delete=models.CASCADE,  # Если скважина удаляется, все связанные суточные рапорты тоже удаляются
        related_name="daily_productions",  # Позволяет получать все рапорты скважины через well.daily_productions
        verbose_name="Скважина",  # Человекочитаемое название поля для форм и админки
    )
    date = models.DateField("Дата")  # Поле даты суточного рапорта
    work_time = models.DecimalField(  # Поле времени работы скважины
        "Время работы, часов",  # Человекочитаемое название поля
        max_digits=4,  # Максимальное количество цифр всего
        decimal_places=2,  # Количество цифр после запятой
        validators=[MinValueValidator(0), MaxValueValidator(24)],  # Значение должно быть от 0 до 24
    )
    liquid_debit = models.DecimalField(  # Поле дебита жидкости
        "Дебит жидкости, м³/сут",  # Человекочитаемое название поля
        max_digits=10,  # Максимальное количество цифр всего
        decimal_places=2,  # Количество цифр после запятой
    )
    water_cut = models.DecimalField(  # Поле обводненности
        "Обводненность, %",  # Человекочитаемое название поля
        max_digits=5,  # Максимальное количество цифр всего
        decimal_places=2,  # Количество цифр после запятой
        validators=[MinValueValidator(0), MaxValueValidator(100)],  # Значение должно быть от 0 до 100
    )
    oil_density = models.DecimalField(  # Поле плотности нефти
        "Плотность нефти, т/м³",  # Человекочитаемое название поля
        max_digits=5,  # Максимальное количество цифр всего
        decimal_places=3,  # Количество цифр после запятой
    )

    class Meta:  # Внутренний класс для дополнительных настроек модели
        constraints = [  # Список ограничений на уровне базы данных
            models.UniqueConstraint(  # Создаем ограничение уникальности
                fields=["well", "date"],  # Комбинация полей well и date не должна повторяться
                name="unique_daily_production_per_well_date",  # Имя ограничения в базе данных
            )
        ]
        verbose_name = "Суточный рапорт"  # Название модели в единственном числе для админки
        verbose_name_plural = "Суточные рапорты"  # Название модели во множественном числе для админки

    def __str__(self):  # Метод для удобного строкового отображения объекта
        return f"{self.well} - {self.date}"  # Возвращаем строку в формате "скважина - дата"
    
    @property  # Делаем метод вычисляемым свойством, чтобы обращаться к нему как к полю
    def calculated_oil(self):
        return self.liquid_debit * (Decimal("1") - self.water_cut / Decimal("100")) * self.oil_density  # Вычисляем расчетный дебит нефти по формуле