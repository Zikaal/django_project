from django.urls import path

from .views import (
    NotificationListView,
    NotificationMarkAllReadView,
    NotificationMarkReadView,
    NotificationPollView,
)

# URL-маршруты приложения notifications.
urlpatterns = [
    # Страница со списком уведомлений текущего пользователя.
    path("", NotificationListView.as_view(), name="notification_list"),

    # Легкий endpoint для опроса из фронтенда:
    # возвращает число непрочитанных и id последнего непрочитанного уведомления.
    path("poll/", NotificationPollView.as_view(), name="notification_poll"),

    # Пометка одного уведомления как прочитанного.
    path("<int:pk>/read/", NotificationMarkReadView.as_view(), name="notification_mark_read"),

    # Пометка всех уведомлений текущего пользователя как прочитанных.
    path("read-all/", NotificationMarkAllReadView.as_view(), name="notification_mark_all_read"),
]