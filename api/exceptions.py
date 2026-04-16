from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Кастомный обработчик исключений DRF.

    Зачем нужен:
    - стандартные ответы DRF могут быть разными по структуре;
    - мобильному приложению и фронтенду удобнее получать единый JSON-формат;
    - здесь мы нормализуем ошибки 400/401/403/404.

    Параметры:
    - exc: пойманное исключение;
    - context: контекст вызова (view, request и т.д.).

    Возвращает:
    - стандартный DRF response, но в унифицированном формате;
    - либо None, если DRF сам не смог обработать исключение.
    """
    response = exception_handler(exc, context)

    # Если DRF не распознал исключение, возвращаем как есть.
    # Обычно это означает, что дальше сработает глобальная обработка 500.
    if response is None:
        return response

    # Ошибка валидации данных.
    if response.status_code == 400:
        response.data = {
            "success": False,
            "message": "Ошибка валидации данных.",
            "errors": response.data,
        }

    # Нет авторизации / не передан токен / токен невалиден.
    elif response.status_code == 401:
        response.data = {
            "success": False,
            "message": "Требуется авторизация.",
        }

    # Есть авторизация, но нет нужных прав.
    elif response.status_code == 403:
        detail = response.data.get("detail", "У вас нет прав для выполнения этого действия.")
        response.data = {
            "success": False,
            "message": str(detail),
        }

    # Объект/маршрут не найден.
    elif response.status_code == 404:
        detail = response.data.get("detail", "Объект не найден.")
        response.data = {
            "success": False,
            "message": str(detail),
        }

    return response