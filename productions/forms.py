from django import forms
from .models import DailyProduction, Well


class DailyProductionForm(forms.ModelForm):
    """
    Форма для создания и редактирования суточного рапорта по добыче нефти (DailyProduction).

    Используется в представлениях CreateView и UpdateView.
    Включает валидацию на уровне формы и дополнительную бизнес-валидацию
    на уникальность записи (одна скважина — одна дата).
    """

    class Meta:
        """
        Метаданные формы ModelForm.
        
        Определяет:
        - Связанную модель
        - Поля, которые будут отображаться в форме
        - Виджеты для полей
        - Сообщения об ошибках для каждого поля
        """
        model = DailyProduction
        fields = [
            "well",
            "date",
            "work_time",
            "liquid_debit",
            "water_cut",
            "oil_density",
        ]
        widgets = {
            # Используем HTML5 input type="date" для удобного выбора даты
            "date": forms.DateInput(attrs={"type": "date"}),
        }
        error_messages = {
            "well": {
                "required": "Выберите скважину.",
                "invalid_choice": "Выберите корректную скважину.",
            },
            "date": {
                "required": "Укажите дату.",
                "invalid": "Введите корректную дату.",
            },
            "work_time": {
                "required": "Укажите время работы.",
                "invalid": "Введите корректное значение времени работы.",
            },
            "liquid_debit": {
                "required": "Укажите дебит жидкости.",
                "invalid": "Введите корректное значение дебита жидкости.",
            },
            "water_cut": {
                "required": "Укажите обводненность.",
                "invalid": "Введите корректное значение обводненности.",
            },
            "oil_density": {
                "required": "Укажите плотность нефти.",
                "invalid": "Введите корректное значение плотности нефти.",
            },
        }

    def clean(self):
        """
        Дополнительная валидация формы на уровне всех полей (clean).

        Проверяет уникальность комбинации "скважина + дата".
        При редактировании записи (UpdateView) исключает текущую запись из проверки,
        чтобы не вызывать ошибку при сохранении без изменения даты.

        Raises:
            forms.ValidationError: Если для выбранной скважины уже существует запись на эту дату.
        """
        cleaned_data = super().clean()

        well = cleaned_data.get("well")
        date = cleaned_data.get("date")

        # Проверяем уникальность только если оба поля заполнены
        if well and date:
            # Формируем запрос на существование записи
            qs = DailyProduction.objects.filter(well=well, date=date)

            # При редактировании исключаем текущую запись
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            # Если такая запись уже существует — выбрасываем ошибку
            if qs.exists():
                raise forms.ValidationError(
                    "Для этой скважины уже есть запись на эту дату."
                )

        return cleaned_data


class WellForm(forms.ModelForm):
    """
    Форма для создания и редактирования скважины (Well).

    Используется в представлениях WellCreateView и WellUpdateView.
    """

    class Meta:
        """
        Метаданные формы ModelForm для модели Well.
        
        Определяет:
        - Связанную модель
        - Поля, которые будут отображаться в форме
        """
        model = Well
        fields = [
            "name",
            "oil_company",
            "type",
            "max_drilling_depth",
            "latitude",
            "longitude",
        ]