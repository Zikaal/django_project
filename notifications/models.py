from django.conf import settings
from django.db import models
from django.utils import timezone


class Notification(models.Model):
    class Level(models.TextChoices):
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
    title = models.CharField("Заголовок", max_length=255)
    message = models.TextField("Сообщение")
    level = models.CharField(
        "Уровень",
        max_length=20,
        choices=Level.choices,
        default=Level.INFO,
    )
    is_read = models.BooleanField("Прочитано", default=False)
    read_at = models.DateTimeField("Прочитано в", blank=True, null=True)

    related_import = models.ForeignKey(
        "productions.DailyProductionImportJob",
        on_delete=models.SET_NULL,
        related_name="notifications",
        blank=True,
        null=True,
        verbose_name="Связанный импорт",
    )
    related_export = models.ForeignKey(
        "productions.MonthlyProductionExportJob",
        on_delete=models.SET_NULL,
        related_name="notifications",
        blank=True,
        null=True,
        verbose_name="Связанный экспорт",
    )

    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ["-created_at"]

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])

    @property
    def badge_class(self):
        return {
            self.Level.INFO: "bg-slate-100 text-slate-700",
            self.Level.SUCCESS: "bg-emerald-100 text-emerald-700",
            self.Level.WARNING: "bg-amber-100 text-amber-700",
            self.Level.ERROR: "bg-rose-100 text-rose-700",
        }.get(self.level, "bg-slate-100 text-slate-700")

    def __str__(self):
        return f"{self.recipient} — {self.title}"