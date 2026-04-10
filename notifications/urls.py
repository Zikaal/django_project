from django.urls import path

from .views import (
    NotificationListView,
    NotificationMarkAllReadView,
    NotificationMarkReadView,
    NotificationPollView,
)

urlpatterns = [
    path("", NotificationListView.as_view(), name="notification_list"),
    path("poll/", NotificationPollView.as_view(), name="notification_poll"),
    path("<int:pk>/read/", NotificationMarkReadView.as_view(), name="notification_mark_read"),
    path("read-all/", NotificationMarkAllReadView.as_view(), name="notification_mark_all_read"),
]