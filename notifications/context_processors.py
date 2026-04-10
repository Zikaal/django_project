from .models import Notification


def notifications_context(request):
    if not request.user.is_authenticated:
        return {
            "unread_notifications_count": 0,
            "recent_notifications": [],
        }

    recent_notifications = list(
        Notification.objects.filter(recipient=request.user)
        .order_by("-created_at")[:5]
    )
    unread_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).count()

    return {
        "unread_notifications_count": unread_count,
        "recent_notifications": recent_notifications,
    }