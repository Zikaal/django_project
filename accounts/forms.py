from django import forms   # Импортируем модуль forms из Django для создания форм

from .models import Profile  # Импортируем модель Profile из текущего приложения

class ProfileForm(forms.ModelForm):  # Создаем форму на основе модели Profile
    class Meta:  # Внутренний класс для настройки формы
        model = Profile  # Указываем, что форма связана с моделью Profile
        fields = ["phone_number","bio"] # поля, которые можно редактировать через форму
        widgets = {  # Настраиваем, как отдельные поля будут отображаться в HTML
            "bio": forms.Textarea(attrs={"rows": 5}), # поле bio отображаем как многострочное текстовое поле высотой в 5 строк
        }