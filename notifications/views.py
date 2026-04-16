from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from .models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    """
    Список уведомлений текущего пользователя.

    Доступ:
    - только для авторизованных пользователей.

    Возможности:
    - показывает только уведомления самого пользователя;
    - поддерживает фильтрацию по статусу: all / unread / read;
    - использует пагинацию.
    """

    model = Notification
    template_name = "notifications/notification_list.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        """
        Возвращает уведомления только текущего пользователя.

        Дополнительно поддерживает GET-параметр status:
        - all: все уведомления;
        - unread: только непрочитанные;
        - read: только прочитанные.
        """
        queryset = Notification.objects.filter(recipient=self.request.user)

        status = self.request.GET.get("status", "all")
        if status == "unread":
            queryset = queryset.filter(is_read=False)
        elif status == "read":
            queryset = queryset.filter(is_read=True)

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        """
        Добавляет в шаблон:
        - выбранный фильтр status;
        - количество непрочитанных уведомлений.
        """
        context = super().get_context_data(**kwargs)
        context["selected_status"] = self.request.GET.get("status", "all")
        context["unread_count"] = Notification.objects.filter(
            recipient=self.request.user,
            is_read=False,
        ).count()
        return context


class NotificationMarkReadView(LoginRequiredMixin, View):
    """
    Помечает одно уведомление как прочитанное.

    Важно:
    - пользователь может менять только свои уведомления;
    - если pk чужой, будет 404, а не доступ к чужим данным.
    """

    def post(self, request, pk):
        notification = get_object_or_404(
            Notification,
            pk=pk,
            recipient=request.user,
        )
        notification.mark_as_read()

        # Возвращаем пользователя туда, откуда он пришел,
        # либо на общий список уведомлений.
        return redirect(request.POST.get("next") or reverse_lazy("notification_list"))


class NotificationMarkAllReadView(LoginRequiredMixin, View):
    """
    Помечает все непрочитанные уведомления текущего пользователя как прочитанные.

    Здесь используется bulk update, а не цикл по объектам,
    что эффективнее по SQL-запросам.
    """

    def post(self, request):
        Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(
            is_read=True,
            read_at=timezone.now(),
        )
        return redirect(request.POST.get("next") or reverse_lazy("notification_list"))


class NotificationPollView(LoginRequiredMixin, View):
    """
    Легкий JSON-endpoint для фронтенда.

    Возвращает:
    - количество непрочитанных уведомлений;
    - id самого нового непрочитанного уведомления.

    Это удобно для периодического polling в navbar/header,
    чтобы обновлять счетчик без полной перезагрузки страницы.
    """

    def get(self, request):
        unread_qs = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).order_by("-created_at")

        latest_unread = unread_qs.first()

        return JsonResponse(
            {
                "unread_count": unread_qs.count(),
                "latest_unread_id": latest_unread.id if latest_unread else None,
            }
        )