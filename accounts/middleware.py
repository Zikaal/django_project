from .current_user import reset_current_user, set_current_user


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        current_user = user if getattr(user, "is_authenticated", False) else None

        token = set_current_user(current_user)
        try:
            response = self.get_response(request)
        finally:
            reset_current_user(token)

        return response