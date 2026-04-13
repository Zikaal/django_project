from django.conf import settings
from django.db import models

from companies.models import OilCompany


class Profile(models.Model):
    """
    Модель профиля пользователя (Profile).

    Расширяет стандартную модель пользователя Django через связь OneToOneField.
    Хранит дополнительную информацию о сотруднике нефтяной компании.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Пользователь",
    )
    oil_company = models.ForeignKey(
        OilCompany,
        on_delete=models.CASCADE,
        related_name="employees",
        verbose_name="Нефтяная компания",
        null=True,
        blank=True,
        error_messages={
            "blank": "Выберите нефтяную компанию.",
            "invalid": "Выберите корректную нефтяную компанию.",
            },
        )
    bio = models.TextField(
        "О себе",
        blank=True,  # рекомендуется добавить, если поле не обязательно
        error_messages={
            "invalid": "Введите корректную информацию о себе.",
        },
    )
    department = models.CharField(
        "Отдел",
        max_length=150,
        error_messages={
            "blank": "Укажите отдел.",
            "invalid": "Введите корректное название отдела.",
        },
    )
    phone_number = models.CharField(
        "Телефон",
        max_length=30,
        error_messages={
            "blank": "Укажите номер телефона.",
            "invalid": "Введите корректный номер телефона.",
        },
    )
    avatar = models.ImageField(
        "Аватар",
        upload_to="avatars/",
        blank=True,
        null=True,
    )

    def __str__(self):
        """
        Строковое представление профиля.
        Возвращает удобочитаемую строку с именем пользователя.
        """
        return f"Профиль пользователя {self.user}"

    class Meta:
        """
        Метаданные модели Profile.
        """

        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"
        ordering = ["user__username"]  # Сортировка по умолчанию по имени пользователя
