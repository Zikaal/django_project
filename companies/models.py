from django.db import models


class OilCompany(models.Model):
    """
    Модель нефтяной компании (OilCompany).

    Хранит базовую информацию о компаниях, занимающихся добычей нефти.
    Используется как связанная модель для скважин (Well) и сотрудников.
    """

    name = models.CharField(
        "Название компании",
        max_length=255,
        unique=True,
        help_text="Уникальное название нефтяной компании"
    )
    region = models.CharField(
        "Регион",
        max_length=255,
        help_text="Регион деятельности компании"
    )

    def __str__(self):
        """
        Строковое представление объекта.
        Возвращается название компании — используется в выпадающих списках,
        админке Django и при выводе в шаблонах.
        """
        return self.name

    class Meta:
        """
        Метаданные модели.
        """
        verbose_name = "Нефтяная компания"
        verbose_name_plural = "Нефтяные компании"
        ordering = ['name']          # Сортировка по умолчанию в QuerySet'ах