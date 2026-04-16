from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts.models import Profile
from companies.models import OilCompany
from productions.models import DailyProduction, Well

# Используем активную модель пользователя проекта.
User = get_user_model()


class MobileApiTests(APITestCase):
    """
    Набор интеграционных API-тестов для мобильного клиента.

    Что проверяется:
    - health endpoint;
    - авторизация и получение token;
    - endpoint /me/;
    - создание суточного рапорта;
    - ограничения по ролям и компаниям;
    - валидация входных данных;
    - защита от дублей.
    """

    def setUp(self):
        """
        Подготавливает тестовое окружение перед каждым тестом.

        Создаем:
        - ролевые группы;
        - две компании;
        - по одной скважине в каждой компании;
        - пользователей разных ролей;
        - url'ы, по которым будут идти запросы.
        """
        self._create_roles()

        self.company_a = OilCompany.objects.create(
            name="KazOil A",
            region="Atyrau",
        )
        self.company_b = OilCompany.objects.create(
            name="KazOil B",
            region="Aktau",
        )

        self.well_a1 = Well.objects.create(
            name="Well-A1",
            oil_company=self.company_a,
            type="Production",
            max_drilling_depth=3200,
            latitude=51.1,
            longitude=52.2,
        )
        self.well_b1 = Well.objects.create(
            name="Well-B1",
            oil_company=self.company_b,
            type="Production",
            max_drilling_depth=3500,
            latitude=53.3,
            longitude=54.4,
        )

        self.admin_user = self._create_user(
            username="admin_user",
            password="testpass123",
            role="Admin",
            company=None,
        )
        self.manager_user = self._create_user(
            username="manager_user",
            password="testpass123",
            role="Manager",
            company=self.company_a,
        )
        self.operator_user = self._create_user(
            username="operator_user",
            password="testpass123",
            role="Operator",
            company=self.company_a,
        )
        self.no_role_user = self._create_user(
            username="no_role_user",
            password="testpass123",
            role=None,
            company=self.company_a,
        )

        self.token_url = reverse("api_token_auth")
        self.me_url = reverse("api_me")
        self.create_report_url = reverse("api_dailyproduction_create")
        self.health_url = reverse("api_health")

    def _create_roles(self):
        """
        Создает базовые группы ролей, если их еще нет.

        Это важно, потому что часть логики проекта завязана именно на Django Groups.
        """
        for role_name in ("Admin", "Manager", "Operator"):
            Group.objects.get_or_create(name=role_name)

    def _create_user(self, username, password, role=None, company=None):
        """
        Вспомогательный метод для создания тестового пользователя.

        Что делает:
        - создает пользователя;
        - при необходимости добавляет в группу роли;
        - создает/обновляет профиль;
        - привязывает профиль к компании.
        """
        user = User.objects.create_user(
            username=username,
            password=password,
            email=f"{username}@example.com",
        )

        if role:
            group = Group.objects.get(name=role)
            user.groups.add(group)

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.oil_company = company
        profile.save()

        return user

    def _auth(self, user):
        """
        Авторизует тестовый клиент по TokenAuthentication.

        Возвращает token на случай, если он понадобится в самом тесте.
        """
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        return token

    def _report_payload(self, well_id):
        """
        Генерирует валидный payload для создания суточного рапорта.

        well_id передается параметром, чтобы быстро проверять:
        - свою скважину;
        - чужую скважину.
        """
        return {
            "well": well_id,
            "date": "2026-04-14",
            "work_time": "24.00",
            "liquid_debit": "125.50",
            "water_cut": "18.20",
            "oil_density": "0.82",
        }

    def test_health_endpoint_returns_200(self):
        """
        Проверяем, что health endpoint отвечает 200 OK
        и возвращает ожидаемую служебную информацию.
        """
        response = self.client.get(self.health_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")
        self.assertEqual(response.data["version"], "v1")

    def test_user_can_get_token(self):
        """
        Проверяем, что пользователь может получить токен по логину/паролю,
        а в ответе возвращается базовая информация о нем.
        """
        response = self.client.post(
            self.token_url,
            {
                "username": "operator_user",
                "password": "testpass123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("token", response.data["data"])
        self.assertEqual(response.data["data"]["role"], "Operator")
        self.assertEqual(response.data["data"]["oil_company"]["id"], self.company_a.id)

    def test_me_endpoint_with_token_returns_user_data(self):
        """
        Проверяем, что endpoint /me/ возвращает данные текущего пользователя
        при наличии валидного токена.
        """
        self._auth(self.operator_user)

        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["username"], "operator_user")
        self.assertEqual(response.data["data"]["role"], "Operator")
        self.assertEqual(response.data["data"]["oil_company"]["id"], self.company_a.id)

    def test_create_daily_report_without_token_returns_401(self):
        """
        Без токена создание рапорта должно быть запрещено.
        """
        response = self.client.post(
            self.create_report_url,
            self._report_payload(self.well_a1.id),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])

    def test_operator_can_create_daily_report_for_own_well(self):
        """
        Operator должен иметь право создать рапорт
        для своей скважины / своей компании.
        """
        self._auth(self.operator_user)

        response = self.client.post(
            self.create_report_url,
            self._report_payload(self.well_a1.id),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(DailyProduction.objects.count(), 1)

        report = DailyProduction.objects.first()
        self.assertEqual(report.well_id, self.well_a1.id)
        self.assertEqual(str(report.date), "2026-04-14")

    def test_operator_cannot_create_daily_report_for_foreign_well(self):
        """
        Operator не должен иметь возможность создать рапорт
        для скважины чужой компании.
        """
        self._auth(self.operator_user)

        response = self.client.post(
            self.create_report_url,
            self._report_payload(self.well_b1.id),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertEqual(DailyProduction.objects.count(), 0)
        self.assertIn("well", response.data["errors"])

    def test_manager_can_create_daily_report_for_own_company_well(self):
        """
        Manager должен иметь возможность создавать рапорт
        для скважины своей компании.
        """
        self._auth(self.manager_user)

        response = self.client.post(
            self.create_report_url,
            self._report_payload(self.well_a1.id),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(DailyProduction.objects.count(), 1)

    def test_admin_can_create_daily_report_for_any_company_well(self):
        """
        Admin может создавать рапорт для любой компании.
        """
        self._auth(self.admin_user)

        response = self.client.post(
            self.create_report_url,
            self._report_payload(self.well_b1.id),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(DailyProduction.objects.count(), 1)
        self.assertEqual(DailyProduction.objects.first().well_id, self.well_b1.id)

    def test_user_without_role_cannot_create_daily_report(self):
        """
        Авторизованный пользователь без бизнес-роли
        не должен иметь доступ к созданию рапортов.
        """
        self._auth(self.no_role_user)

        response = self.client.post(
            self.create_report_url,
            self._report_payload(self.well_a1.id),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])
        self.assertEqual(DailyProduction.objects.count(), 0)

    def test_invalid_payload_returns_400(self):
        """
        Проверяем валидацию входных данных.
        Например, water_cut = 150.00 должен считаться некорректным.
        """
        self._auth(self.operator_user)

        payload = self._report_payload(self.well_a1.id)
        payload["water_cut"] = "150.00"

        response = self.client.post(
            self.create_report_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("water_cut", response.data["errors"])

    def test_duplicate_daily_report_returns_400(self):
        """
        Проверяем защиту от дублирования:
        нельзя создать второй рапорт на ту же дату для той же скважины.
        """
        DailyProduction.objects.create(
            well=self.well_a1,
            date="2026-04-14",
            work_time="24.00",
            liquid_debit="120.00",
            water_cut="15.00",
            oil_density="0.80",
        )

        self._auth(self.operator_user)

        response = self.client.post(
            self.create_report_url,
            self._report_payload(self.well_a1.id),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("date", response.data["errors"])
        self.assertEqual(DailyProduction.objects.count(), 1)