from django.conf import settings
from django.db import models
from django.utils import timezone


class Notification(models.Model):
    """
    Модель уведомления пользователя.

    Для чего нужна:
    - хранит служебные и бизнес-уведомления в системе;
    - позволяет отслеживать, прочитал ли пользователь сообщение;
    - может быть связана с задачами импорта и экспорта.

    Примеры сценариев:
    - импорт успешно завершен;
    - экспорт готов к скачиванию;
    - произошла ошибка при обработке файла;
    - пользователь получил системное предупреждение.
    """

    class Level(models.TextChoices):
        """
        Возможные уровни уведомления.

        Используются для:
        - визуального оформления в UI;
        - смыслового разделения уведомлений по важности.
        """

        INFO = "info", "Информация"
        SUCCESS = "success", "Успех"
        WARNING = "warning", "Предупреждение"
        ERROR = "error", "Ошибка"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Получатель",
    )
    # Пользователь, которому предназначено уведомление.
    # При удалении пользователя его уведомления тоже удаляются.

    title = models.CharField("Заголовок", max_length=255)
    # Короткий заголовок уведомления.

    message = models.TextField("Сообщение")
    # Основной текст уведомления.

    level = models.CharField(
        "Уровень",
        max_length=20,
        choices=Level.choices,
        default=Level.INFO,
    )
    # Тип уведомления, влияющий на отображение и смысл.

    is_read = models.BooleanField("Прочитано", default=False)
    # Флаг прочитанности.

    read_at = models.DateTimeField("Прочитано в", blank=True, null=True)
    # Дата и время, когда уведомление было прочитано.

    related_import = models.ForeignKey(
        "productions.DailyProductionImportJob",
        on_delete=models.SET_NULL,
        related_name="notifications",
        blank=True,
        null=True,
        verbose_name="Связанный импорт",
    )
    # Ссылка на задачу импорта, если уведомление относится к импорту.
    # SET_NULL выбран правильно: если импорт-объект удалят, уведомление останется.

    related_export = models.ForeignKey(
        "productions.MonthlyProductionExportJob",
        on_delete=models.SET_NULL,
        related_name="notifications",
        blank=True,
        null=True,
        verbose_name="Связанный экспорт",
    )
    # Ссылка на задачу экспорта, если уведомление относится к экспорту.

    created_at = models.DateTimeField("Создано", auto_now_add=True)
    # Время создания уведомления.

    class Meta:
        """
        Метаданные модели.
        """

        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ["-created_at"]

    def mark_as_read(self):
        """
        Помечает уведомление как прочитанное.

        Что делает:
        - ставит is_read=True;
        - записывает read_at текущим временем;
        - сохраняет только измененные поля.

        Почему проверяем not self.is_read:
        - чтобы не делать лишний update, если уведомление уже было прочитано.
        """
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])

    @property
    def badge_class(self):
        """
        Возвращает CSS-класс для отображения бейджа уведомления в шаблоне.

        Зачем это удобно:
        - логика выбора цвета лежит рядом с моделью;
        - шаблон получает уже готовое значение;
        - меньше условных if/elif прямо в HTML.
        """
        return {
            self.Level.INFO: "bg-slate-100 text-slate-700",
            self.Level.SUCCESS: "bg-emerald-100 text-emerald-700",
            self.Level.WARNING: "bg-amber-100 text-amber-700",
            self.Level.ERROR: "bg-rose-100 text-rose-700",
        }.get(self.level, "bg-slate-100 text-slate-700")

    def __str__(self):
        """
        Человекочитаемое строковое представление уведомления.
        """
        return f"{self.recipient} — {self.title}"
