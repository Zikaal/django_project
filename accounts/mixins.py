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
    """
    Базовый mixin для проверки Django permissions.

    Идея:
    - view может задать required_permissions;
    - mixin проверит, есть ли у пользователя все нужные permissions;
    - если прав не хватает, будет выброшен PermissionDenied.

    Этот mixin сам по себе не проверяет авторизацию и роль.
    Он отвечает только за permission-коды.
    """

    # Кортеж permission-кодов, которые обязательны для доступа.
    # Пример:
    # required_permissions = ("productions.view_dailyproduction",)
    required_permissions: tuple[str, ...] = ()

    # Сообщение, которое получит пользователь при нехватке прав.
    permission_denied_message = "У вас недостаточно прав для выполнения этого действия."

    def has_required_permissions(self, user) -> bool:
        """
        Проверяет, есть ли у пользователя все permissions,
        перечисленные в required_permissions.

        Логика вынесена в отдельный метод, чтобы:
        - можно было переопределить проверку в дочерних классах;
        - код dispatch оставался компактным;
        - логику было проще тестировать отдельно.
        """
        return has_all_permissions(user, self.required_permissions)

    def enforce_required_permissions(self, user) -> None:
        """
        Принудительно проверяет permissions и выбрасывает исключение,
        если прав не хватает.

        Используется внутри dispatch у role-based mixin'ов.
        """
        if not self.has_required_permissions(user):
            raise PermissionDenied(self.permission_denied_message)


class CompanyScopedMixin:
    """
    Mixin для ограничения queryset по компании пользователя.

    Для кого нужен:
    - Manager и Operator обычно должны видеть только данные своей компании;
    - Admin видит все данные без ограничений.

    Как работает:
    - ожидает, что у view есть get_queryset() в родительском классе;
    - берет queryset из super();
    - если пользователь не Admin, фильтрует данные по company id.

    Важно:
    - поле фильтра задается через company_filter_field;
    - это позволяет использовать mixin с разными моделями,
      где связь с компанией может называться по-разному.
    """

    # Название поля, по которому будет накладываться фильтр.
    # По умолчанию считается, что в модели есть поле oil_company_id.
    # Если в модели связь глубже, можно переопределить, например:
    # company_filter_field = "well__oil_company_id"
    company_filter_field: str = "oil_company_id"

    def get_queryset(self):
        """
        Возвращает queryset, ограниченный компанией пользователя.

        Логика:
        - Admin -> полный queryset;
        - пользователь без компании -> пустой queryset;
        - все остальные -> только объекты своей компании.
        """
        queryset = super().get_queryset()

        # Администратор не ограничен одной компанией.
        if is_admin(self.request.user):
            return queryset

        # Для Manager/Operator берем компанию из профиля пользователя.
        company_id = get_user_company_id(self.request.user)

        # Если компания отсутствует, безопаснее ничего не показывать.
        if company_id is None:
            return queryset.none()

        # Фильтруем по указанному полю.
        return queryset.filter(**{self.company_filter_field: company_id})


class AdminRequiredMixin(PermissionAwareMixin, LoginRequiredMixin):
    """
    Mixin для страниц, доступных только администраторам.

    Проверяет по шагам:
    1. Пользователь должен быть авторизован.
    2. Пользователь должен быть Admin.
    3. Пользователь должен иметь все required_permissions,
       если они указаны.

    Почему используется и роль, и permissions:
    - роль задает бизнес-уровень доступа;
    - permissions дают более точный контроль над конкретными действиями.
    """

    def dispatch(self, request, *args, **kwargs):
        # Если пользователь не вошел в систему,
        # LoginRequiredMixin перенаправит его на страницу логина.
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Даже авторизованный пользователь без роли Admin сюда пройти не должен.
        if not is_admin(request.user):
            raise PermissionDenied("Этот раздел доступен только администраторам.")

        # Проверяем дополнительные Django permissions, если они указаны.
        self.enforce_required_permissions(request.user)

        return super().dispatch(request, *args, **kwargs)


class AdminOrManagerMixin(PermissionAwareMixin, LoginRequiredMixin):
    """
    Mixin для страниц, доступных администраторам и менеджерам.

    Подходит для разделов, где:
    - админ видит все;
    - менеджер тоже имеет доступ;
    - оператор не должен иметь доступ.

    Например:
    - списки компаний,
    - справочники,
    - dashboard,
    - импорт/экспорт.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Разрешаем доступ только Admin и Manager.
        if not (is_admin(request.user) or is_manager(request.user)):
            raise PermissionDenied("Этот раздел доступен только администраторам и менеджерам.")

        # Дополнительно проверяем permissions.
        self.enforce_required_permissions(request.user)

        return super().dispatch(request, *args, **kwargs)


class AnyRoleMixin(PermissionAwareMixin, LoginRequiredMixin):
    """
    Mixin для страниц, куда допускается любой пользователь с системной ролью.

    Подходит для случаев, когда:
    - Admin, Manager и Operator все могут пользоваться разделом;
    - но пользователь без роли вообще не должен получать доступ.

    Пример:
    - список рапортов,
    - просмотр собственных рабочих данных,
    - создание записей в пределах своей роли.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Если у пользователя нет ни одной системной роли,
        # доступ запрещаем с понятным сообщением.
        if not has_any_role(request.user):
            raise PermissionDenied("Доступ закрыт. Обратитесь к администратору для назначения роли.")

        # Проверяем дополнительные permissions.
        self.enforce_required_permissions(request.user)

        return super().dispatch(request, *args, **kwargs)


class AdminOrManagerScopedMixin(AdminOrManagerMixin, CompanyScopedMixin):
    """
    Комбинированный mixin:
    - допускает только Admin и Manager;
    - при этом автоматически ограничивает queryset по компании.

    Практический смысл:
    - Admin увидит все записи;
    - Manager увидит только записи своей компании.

    Полезен для ListView/CRUD страниц по данным,
    которые привязаны к нефтяной компании.
    """

    pass


class AnyRoleScopedMixin(AnyRoleMixin, CompanyScopedMixin):
    """
    Комбинированный mixin:
    - допускает любого пользователя с ролью;
    - автоматически ограничивает queryset по компании.

    Практический смысл:
    - Admin увидит все данные;
    - Manager и Operator увидят только свою компанию.

    Это удобно для рапортов, скважин, производственных записей и других
    company-scoped сущностей.
    """

    pass
