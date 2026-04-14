from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return response

    if response.status_code == 400:
        response.data = {
            "success": False,
            "message": "Ошибка валидации данных.",
            "errors": response.data,
        }

    elif response.status_code == 401:
        response.data = {
            "success": False,
            "message": "Требуется авторизация.",
        }

    elif response.status_code == 403:
        detail = response.data.get("detail", "У вас нет прав для выполнения этого действия.")
        response.data = {
            "success": False,
            "message": str(detail),
        }

    elif response.status_code == 404:
        detail = response.data.get("detail", "Объект не найден.")
        response.data = {
            "success": False,
            "message": str(detail),
        }

    return response