from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from .utils import (
    get_user_company_id,
    has_all_permissions,
    has_any_role,
    is_admin,
    is_manager,
)


class PermissionAwareMixin:
    required_permissions: tuple[str, ...] = ()
    permission_denied_message = "У вас недостаточно прав для выполнения этого действия."

    def has_required_permissions(self, user) -> bool:
        return has_all_permissions(user, self.required_permissions)

    def enforce_required_permissions(self, user) -> None:
        if not self.has_required_permissions(user):
            raise PermissionDenied(self.permission_denied_message)


class CompanyScopedMixin:
    company_filter_field: str = "oil_company_id"

    def get_queryset(self):
        queryset = super().get_queryset()
        if is_admin(self.request.user):
            return queryset

        company_id = get_user_company_id(self.request.user)
        if company_id is None:
            return queryset.none()

        return queryset.filter(**{self.company_filter_field: company_id})


class AdminRequiredMixin(PermissionAwareMixin, LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not is_admin(request.user):
            raise PermissionDenied("Этот раздел доступен только администраторам.")
        self.enforce_required_permissions(request.user)
        return super().dispatch(request, *args, **kwargs)


class AdminOrManagerMixin(PermissionAwareMixin, LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (is_admin(request.user) or is_manager(request.user)):
            raise PermissionDenied("Этот раздел доступен только администраторам и менеджерам.")
        self.enforce_required_permissions(request.user)
        return super().dispatch(request, *args, **kwargs)


class AnyRoleMixin(PermissionAwareMixin, LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not has_any_role(request.user):
            raise PermissionDenied(
                "Доступ закрыт. Обратитесь к администратору для назначения роли."
            )
        self.enforce_required_permissions(request.user)
        return super().dispatch(request, *args, **kwargs)


class AdminOrManagerScopedMixin(AdminOrManagerMixin, CompanyScopedMixin):
    pass


class AnyRoleScopedMixin(AnyRoleMixin, CompanyScopedMixin):
    pass