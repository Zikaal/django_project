from django import forms
from .models import DailyProduction


class DailyProductionForm(forms.ModelForm):
    class Meta:
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
        cleaned_data = super().clean()

        well = cleaned_data.get("well")
        date = cleaned_data.get("date")

        if well and date:
            qs = DailyProduction.objects.filter(well=well, date=date)

            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise forms.ValidationError(
                    "Для этой скважины уже есть запись на эту дату."
                )

        return cleaned_data