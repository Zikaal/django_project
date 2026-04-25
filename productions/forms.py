from django import forms

from .models import DailyProduction, Well


class DailyProductionForm(forms.ModelForm):
    """
    Форма создания и редактирования суточного рапорта DailyProduction.

    Где используется:
    - DailyProductionCreateView
    - DailyProductionUpdateView

    За что отвечает:
    - показывает пользователю поля рапорта;
    - задает удобный виджет для даты;
    - возвращает понятные сообщения об ошибках;
    - дополнительно проверяет бизнес-правило:
      для одной скважины нельзя создать два рапорта на одну дату.
    """

    class Meta:
        """
        Метаданные ModelForm.

        Здесь указываем:
        - связанную модель;
        - список полей, которые можно редактировать через форму;
        - HTML-виджеты;
        - пользовательские сообщения об ошибках.
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
            # HTML5 date input делает выбор даты удобнее в браузере.
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
        Общая валидация формы после очистки отдельных полей.

        Проверяем бизнес-ограничение:
        одна скважина не может иметь больше одного рапорта на одну и ту же дату.

        Почему это делается здесь:
        - пользователь сразу получает понятную ошибку на уровне формы;
        - это дополняет защиту на уровне модели/БД.

        Особенность:
        - при редактировании текущую запись исключаем из проверки,
          иначе форма всегда считала бы ее дубликатом самой себя.
        """
        cleaned_data = super().clean()

        well = cleaned_data.get("well")
        date = cleaned_data.get("date")

        # Проверяем уникальность только если оба поля уже корректно заполнены.
        if well and date:
            qs = DailyProduction.objects.filter(well=well, date=date)

            # Если это редактирование существующей записи,
            # исключаем ее из поиска дубликатов.
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise forms.ValidationError("Для этой скважины уже есть запись на эту дату.")

        return cleaned_data


class WellForm(forms.ModelForm):
    """
    Форма создания и редактирования скважины.

    Где используется:
    - WellCreateView
    - WellUpdateView

    Примечание:
    - сама форма простая и почти полностью опирается на валидацию модели Well;
    - ограничение доступных компаний для Manager делается не здесь,
      а во view через helper _scope_company_in_form().
    """

    class Meta:
        """
        Метаданные формы для модели Well.
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


class DailyProductionImportForm(forms.Form):
    """
    Простая форма загрузки Excel-файла для импорта рапортов.

    Используется в DailyProductionImportView.

    Здесь нет сложной бизнес-логики:
    - форма только принимает файл;
    - дальнейшая обработка идет в фоне через Celery-задачу импорта.
    """

    file = forms.FileField(
        label="Excel-файл с рапортами",
        help_text="Загрузите .xlsx файл с недельными или дневными рапортами",
    )


class MonthlyProductionExportForm(forms.Form):
    """
    Простая форма запуска месячного экспорта.

    Используется в MonthlyProductionExportView.

    Пользователь указывает:
    - год;
    - месяц.

    После валидации форма не создает файл сама,
    а только передает данные во view, где создается export job
    и запускается фоновая Celery-задача.
    """

    year = forms.IntegerField(
        label="Год",
        min_value=2000,
        max_value=2100,
    )

    month = forms.IntegerField(
        label="Месяц",
        min_value=1,
        max_value=12,
    )
