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
    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        level=level,
        related_import=related_import,
        related_export=related_export,
    )