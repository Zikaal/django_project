from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Настройка Django Admin для модели Notification.

    Что дает:
    - удобный просмотр уведомлений в админке;
    - фильтрацию по уровню, статусу прочтения и дате создания;
    - поиск по получателю, заголовку и тексту сообщения.

    Полезно для:
    - отладки уведомлений;
    - проверки, кому и что было отправлено;
    - ручного анализа импорта/экспорта через связанные уведомления.
    """

    # Колонки, которые видны в списке уведомлений.
    list_display = (
        "id",
        "recipient",
        "title",
        "level",
        "is_read",
        "created_at",
        "read_at",
    )

    # Боковые фильтры справа в админке.
    list_filter = ("level", "is_read", "created_at")

    # Поля, по которым работает поиск.
    search_fields = ("recipient__username", "recipient__email", "title", "message")

    # Поля только для чтения.
    # Обычно даты создания/прочтения не редактируют вручную.
    readonly_fields = ("created_at", "read_at")
