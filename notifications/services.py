from .models import Notification


def create_notification(
    *,
    recipient,
    title: str,
    message: str,
    level: str = Notification.Level.INFO,
    related_import=None,
    related_export=None,
):
    """
    Сервисная функция для создания уведомления.

    Почему это лучше, чем везде писать Notification.objects.create(...):
    - создается единая точка входа для логики уведомлений;
    - если позже понадобится дополнительная логика
      (логирование, шаблоны сообщений, отправка email/push),
      ее можно будет добавить здесь;
    - внешний код остается чище и проще.

    Параметры:
    - recipient: пользователь-получатель;
    - title: короткий заголовок уведомления;
    - message: основной текст;
    - level: уровень уведомления (info/success/warning/error);
    - related_import: связанный объект импорта, если есть;
    - related_export: связанный объект экспорта, если есть.
    """
    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        level=level,
        related_import=related_import,
        related_export=related_export,
    )