from .models import Notification


def notifications_context(request):
    """
    Добавляет уведомления текущего пользователя в контекст шаблонов.

    Что возвращает:
    - unread_notifications_count: количество непрочитанных уведомлений;
    - recent_notifications: последние 5 уведомлений пользователя.

    Зачем нужен context processor:
    - чтобы header/navbar мог показывать счетчик уведомлений на всех страницах;
    - чтобы можно было быстро вывести небольшой dropdown последних уведомлений
      без дублирования этой логики в каждом отдельном view.
    """

    # Для неавторизованного пользователя уведомления не нужны.
    if not request.user.is_authenticated:
        return {
            "unread_notifications_count": 0,
            "recent_notifications": [],
        }

    # Последние 5 уведомлений пользователя.
    recent_notifications = list(Notification.objects.filter(recipient=request.user).order_by("-created_at")[:5])

    # Отдельно считаем число непрочитанных.
    unread_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).count()

    return {
        "unread_notifications_count": unread_count,
        "recent_notifications": recent_notifications,
    }
