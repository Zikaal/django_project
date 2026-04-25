from .current_user import reset_current_user, set_current_user


class CurrentUserMiddleware:
    """
    Middleware для сохранения текущего пользователя в ContextVar
    на время обработки одного HTTP-запроса.

    Зачем это нужно:
    - иногда внутри signals, сервисов, audit-логики или model-layer
      нет прямого доступа к request;
    - но при этом нужно знать, КТО именно выполнил действие;
    - middleware кладет текущего пользователя в thread/context-local хранилище,
      откуда его потом можно получить через get_current_user().

    Это особенно полезно для:
    - аудита изменений;
    - журналирования действий;
    - автоматического заполнения полей вроде created_by / updated_by;
    - логики в signals, где request напрямую недоступен.
    """

    def __init__(self, get_response):
        """
        Стандартная инициализация middleware.

        Django передает сюда следующий обработчик цепочки middleware/view.
        Его нужно сохранить, чтобы потом вызвать.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Основная точка входа middleware.

        Что происходит:
        1. Пытаемся получить request.user.
        2. Если пользователь авторизован — сохраняем его в ContextVar.
        3. Передаем управление дальше по цепочке middleware / во view.
        4. В блоке finally обязательно очищаем ContextVar,
           чтобы данные не "утекли" в следующий запрос.

        Почему finally критически важен:
        - даже если внутри view случится ошибка,
          текущий пользователь должен быть сброшен;
        - иначе можно получить очень опасные баги с "залипанием" пользователя
          между разными запросами.
        """
        # Берем пользователя из request, если Django AuthenticationMiddleware
        # уже добавил его в объект запроса.
        user = getattr(request, "user", None)

        # Сохраняем только авторизованного пользователя.
        # Для анонимного посетителя кладем None.
        current_user = user if getattr(user, "is_authenticated", False) else None

        # set_current_user(...) возвращает token,
        # который потом нужен для корректного reset().
        token = set_current_user(current_user)

        try:
            # Передаем запрос дальше — в следующие middleware и затем во view.
            response = self.get_response(request)
        finally:
            # Обязательно очищаем ContextVar после завершения запроса.
            reset_current_user(token)

        return response
