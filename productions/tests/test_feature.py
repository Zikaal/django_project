from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from companies.models import OilCompany
from productions.models import DailyProduction, Well

# Получаем активную модель пользователя проекта.
User = get_user_model()


class WellFeatureTests(TestCase):
    """
    Feature-тесты для пользовательских сценариев работы со скважинами.

    Что проверяют:
    - доступ к странице создания скважины;
    - поведение для гостя;
    - успешное создание скважины через HTML-форму.
    """

    def setUp(self):
        """
        Подготавливаем базовые тестовые данные:
        - компанию, к которой будет привязана скважина;
        - обычного пользователя, через которого тестируем сценарии.
        """
        self.company = OilCompany.objects.create(
            name="North Oil",
            region="Atyrau",
        )
        self.user = User.objects.create_user(
            username="tester",
            password="TestPass123",
        )

    def test_guest_cannot_open_well_create_page(self):
        """
        Гость не должен иметь доступ к странице создания скважины.

        Ожидаем:
        - редирект (302);
        - переход на страницу логина.
        """
        response = self.client.get(reverse("well_create"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_authenticated_user_can_create_well(self):
        """
        Проверяем, что авторизованный пользователь может отправить форму
        создания скважины и после этого:
        - получить редирект на список скважин;
        - увидеть, что запись реально появилась в БД.

        Это именно feature-тест:
        он проверяет не только форму, но и view + URL + redirect + сохранение.
        """
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("well_create"),
            data={
                "name": "Well-500",
                "oil_company": self.company.id,
                "type": "Exploration",
                "max_drilling_depth": 4200,
                "latitude": "43.250000",
                "longitude": "76.950000",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("well_list"))
        self.assertTrue(Well.objects.filter(name="Well-500").exists())


class DailyProductionFeatureTests(TestCase):
    """
    Feature-тесты для пользовательских сценариев работы с суточными рапортами.

    Что проверяют:
    - успешное создание рапорта через форму;
    - отказ при попытке создать дубликат well + date.
    """

    def setUp(self):
        """
        Подготавливаем тестовые данные:
        - компанию;
        - пользователя;
        - скважину, к которой будут привязаны рапорты.
        """
        self.company = OilCompany.objects.create(
            name="South Oil",
            region="Aktobe",
        )
        self.user = User.objects.create_user(
            username="reporter",
            password="TestPass123",
        )
        self.well = Well.objects.create(
            name="Well-700",
            oil_company=self.company,
            type="Production",
            max_drilling_depth=3900,
            latitude=Decimal("43.111111"),
            longitude=Decimal("76.222222"),
        )

    def test_authenticated_user_can_create_daily_production(self):
        """
        Проверяем стандартный сценарий:
        авторизованный пользователь отправляет форму и успешно создает рапорт.

        Ожидаем:
        - HTTP 302 после POST;
        - редирект на список рапортов;
        - наличие новой записи в БД.
        """
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("dailyproduction_create"),
            data={
                "well": self.well.id,
                "date": "2026-04-02",
                "work_time": "12.00",
                "liquid_debit": "90.00",
                "water_cut": "25.00",
                "oil_density": "0.84",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("dailyproduction_list"))
        self.assertTrue(
            DailyProduction.objects.filter(
                well=self.well,
                date=date(2026, 4, 2),
            ).exists()
        )

    def test_duplicate_daily_production_is_rejected(self):
        """
        Проверяем защиту от дублей.

        Сначала создаем рапорт на ту же скважину и дату,
        затем пытаемся отправить форму еще раз.

        Ожидаем:
        - страница не делает редирект, а возвращается с ошибкой (HTTP 200);
        - в ответе есть сообщение о дублировании;
        - количество записей в БД остается равным 1.
        """
        DailyProduction.objects.create(
            well=self.well,
            date=date(2026, 4, 2),
            work_time=Decimal("10.00"),
            liquid_debit=Decimal("60.00"),
            water_cut=Decimal("10.00"),
            oil_density=Decimal("0.80"),
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse("dailyproduction_create"),
            data={
                "well": self.well.id,
                "date": "2026-04-02",
                "work_time": "11.00",
                "liquid_debit": "75.00",
                "water_cut": "20.00",
                "oil_density": "0.82",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Для этой скважины уже есть запись на эту дату.")
        self.assertEqual(
            DailyProduction.objects.filter(
                well=self.well,
                date=date(2026, 4, 2),
            ).count(),
            1,
        )
