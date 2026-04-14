from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts.models import Profile
from companies.models import OilCompany
from productions.models import DailyProduction, Well

User = get_user_model()


class MobileApiTests(APITestCase):
    def setUp(self):
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
        for role_name in ("Admin", "Manager", "Operator"):
            Group.objects.get_or_create(name=role_name)

    def _create_user(self, username, password, role=None, company=None):
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
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        return token

    def _report_payload(self, well_id):
        return {
            "well": well_id,
            "date": "2026-04-14",
            "work_time": "24.00",
            "liquid_debit": "125.50",
            "water_cut": "18.20",
            "oil_density": "0.82",
        }

    def test_health_endpoint_returns_200(self):
        response = self.client.get(self.health_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")
        self.assertEqual(response.data["version"], "v1")

    def test_user_can_get_token(self):
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
        self._auth(self.operator_user)

        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["username"], "operator_user")
        self.assertEqual(response.data["data"]["role"], "Operator")
        self.assertEqual(response.data["data"]["oil_company"]["id"], self.company_a.id)

    def test_create_daily_report_without_token_returns_401(self):
        response = self.client.post(
            self.create_report_url,
            self._report_payload(self.well_a1.id),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])

    def test_operator_can_create_daily_report_for_own_well(self):
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