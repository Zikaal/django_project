from django.db import models # Импортируем модуль models из Django для создания моделей базы данных
from django.conf import settings  # Импортируем settings, чтобы использовать модель пользователя из настроек проекта

class Profile(models.Model): # Создаем модель Profile, которая будет хранить дополнительную информацию о пользователе
    user = models.OneToOneField(  # Поле связи один-к-одному: одному пользователю соответствует один профиль
        settings.AUTH_USER_MODEL,  # Берем модель пользователя из настроек Django
        on_delete=models.CASCADE,  # Если пользователь удаляется, связанный профиль тоже удаляется
        related_name="profile",  # Позволяет обращаться к профилю через user.profile
    )
    bio = models.TextField("О себе", blank=True, default="")
    department = models.CharField("Отдел", max_length=150, blank=True, default="")
    phone_number = models.CharField("Телефон", max_length=30, blank=True, default="")

    def __str__(self):  # Метод, который задает удобное строковое представление объекта
        return f"Профиль пользователя {self.user}"  # Возвращаем строку, которая будет показываться, например, в админке
