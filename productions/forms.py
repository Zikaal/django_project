from django import forms

from .models import DailyProduction

class DailyProductionForm(forms.ModelForm):  # Создаем форму на основе модели DailyProduction
    class Meta:  # Внутренний класс для настройки формы
        model = DailyProduction  # Указываем, что форма связана с моделью DailyProduction
        fields = [  # Перечисляем поля модели, которые будут доступны для ввода и редактирования в форме
            "well",  # Поле выбора скважины
            "date",  # Поле даты
            "work_time",  # Поле времени работы
            "liquid_debit",  # Поле дебита жидкости
            "water_cut",  # Поле обводненности
            "oil_density",  # Поле плотности нефти
        ]
        widgets = {  # Настраиваем, как отдельные поля будут отображаться в HTML
            "date": forms.DateInput(attrs={"type": "date"}),  # Поле даты отображаем как календарь/дату в HTML5
        }

    def clean(self):  # Переопределяем общий метод валидации формы
        cleaned_data = super().clean()  # Сначала запускаем стандартную очистку и валидацию формы Django

        well = cleaned_data.get("well")  # Получаем значение поля well после очистки
        date = cleaned_data.get("date")  # Получаем значение поля date после очистки

        if well and date:  # Продолжаем проверку только если скважина выбрана и дата заполнена
            qs = DailyProduction.objects.filter(well=well, date=date)  # Ищем в базе записи с такой же скважиной и такой же датой

            if self.instance.pk:  # Проверяем, редактируем ли мы уже существующую запись
                qs = qs.exclude(pk=self.instance.pk)  # Исключаем текущую запись из проверки, чтобы она не считалась дубликатом самой себя

            if qs.exists():  # Если в базе уже есть другая запись с такой же скважиной и датой
                raise forms.ValidationError(  # Выбрасываем ошибку валидации формы
                    "Для этой скважины уже есть запись на эту дату."  # Сообщение об ошибке для пользователя
                )

        return cleaned_data  # Возвращаем очищенные и проверенные данные формы
