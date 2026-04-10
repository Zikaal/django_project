from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from .models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = "notifications/notification_list.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        queryset = Notification.objects.filter(recipient=self.request.user)

        status = self.request.GET.get("status", "all")
        if status == "unread":
            queryset = queryset.filter(is_read=False)
        elif status == "read":
            queryset = queryset.filter(is_read=True)

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_status"] = self.request.GET.get("status", "all")
        context["unread_count"] = Notification.objects.filter(
            recipient=self.request.user,
            is_read=False,
        ).count()
        return context


class NotificationMarkReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(
            Notification,
            pk=pk,
            recipient=request.user,
        )
        notification.mark_as_read()
        return redirect(request.POST.get("next") or reverse_lazy("notification_list"))


class NotificationMarkAllReadView(LoginRequiredMixin, View):
    def post(self, request):
        Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(
            is_read=True,
            read_at=timezone.now(),
        )
        return redirect(request.POST.get("next") or reverse_lazy("notification_list"))