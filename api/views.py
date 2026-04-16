from rest_framework import status
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.utils import get_user_company, get_user_role
from productions.serializers import (
    DailyProductionCreateSerializer,
    DailyProductionReadSerializer,
)

from .permissions import CanCreateDailyProduction, HasAnyBusinessRole


class ApiHealthView(APIView):
    """
    Служебный endpoint для проверки доступности API.

    Обычно используется:
    - мониторингом;
    - мобильным клиентом перед началом работы;
    - devops/infra для health-check.
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """
        Возвращает простой JSON со статусом сервиса.
        """
        return Response(
            {
                "status": "ok",
                "service": "api",
                "version": "v1",
            },
            status=status.HTTP_200_OK,
        )


class MobileObtainAuthTokenView(ObtainAuthToken):
    """
    Кастомный endpoint логина для мобильного клиента.

    В отличие от стандартного ObtainAuthToken,
    этот endpoint возвращает не только token,
    но и базовую информацию о пользователе:
    - id
    - username
    - email
    - role
    - company
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Проверяет логин/пароль и выдает token.

        Алгоритм:
        1. Валидируем credentials через встроенный serializer DRF.
        2. Получаем или создаем token пользователя.
        3. Собираем расширенный JSON-ответ для мобильного приложения.
        """
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)

        company = get_user_company(user)

        return Response(
            {
                "success": True,
                "message": "Авторизация выполнена успешно.",
                "data": {
                    "token": token.key,
                    "user_id": user.pk,
                    "username": user.username,
                    "email": user.email,
                    "role": get_user_role(user),
                    "oil_company": {
                        "id": company.id,
                        "name": company.name,
                    } if company else None,
                },
            },
            status=status.HTTP_200_OK,
        )


class ApiMeView(APIView):
    """
    Endpoint текущего пользователя.

    Возвращает информацию о том,
    кто сейчас авторизован по токену или сессии.
    """

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Возвращает профильную информацию текущего пользователя.
        """
        company = get_user_company(request.user)

        return Response(
            {
                "success": True,
                "message": "Данные пользователя получены успешно.",
                "data": {
                    "user_id": request.user.pk,
                    "username": request.user.username,
                    "email": request.user.email,
                    "role": get_user_role(request.user),
                    "oil_company": {
                        "id": company.id,
                        "name": company.name,
                    } if company else None,
                },
            },
            status=status.HTTP_200_OK,
        )


class DailyProductionCreateApiView(APIView):
    """
    POST /api/v1/reports/daily/

    Endpoint для создания суточного производственного рапорта
    из мобильного приложения.
    """

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, HasAnyBusinessRole, CanCreateDailyProduction]

    def post(self, request, *args, **kwargs):
        """
        Создает новый суточный рапорт.

        Логика:
        1. Проверяем авторизацию и базовые permissions.
        2. Передаем входные данные в serializer.
        3. Serializer выполняет бизнес-валидацию и сохранение.
        4. Возвращаем уже сохраненный объект в "read"-формате.

        Важно:
        - write serializer и read serializer разделены;
        - это удобно, когда входной и выходной формат API различаются.
        """
        serializer = DailyProductionCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        response_serializer = DailyProductionReadSerializer(instance)

        return Response(
            {
                "success": True,
                "message": "Суточный рапорт успешно создан.",
                "data": response_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )