from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from companies.models import OilCompany
from productions.models import DailyProduction, Well

User = get_user_model()


class WellFeatureTests(TestCase):
    def setUp(self):
        self.company = OilCompany.objects.create(
            name="North Oil",
            region="Atyrau",
        )

        self.manager_group, _ = Group.objects.get_or_create(name="Manager")
        well_perms = Permission.objects.filter(
            content_type__app_label="productions",
            codename__in=["add_well", "view_well"],
        )
        self.manager_group.permissions.add(*well_perms)

        self.user = User.objects.create_user(
            username="tester",
            password="TestPass123",
        )
        self.user.groups.add(self.manager_group)
        Profile.objects.update_or_create(
            user=self.user,
            defaults={
                "oil_company": self.company,
                "department": "IT",
                "phone_number": "+77001234567",
                "bio": "",
            },
        )

    def test_guest_cannot_open_well_create_page(self):
        response = self.client.get(reverse("well_create"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_authenticated_user_can_create_well(self):
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
    def setUp(self):
        self.company = OilCompany.objects.create(
            name="South Oil",
            region="Aktobe",
        )

        self.manager_group, _ = Group.objects.get_or_create(name="Manager")
        report_perms = Permission.objects.filter(
            content_type__app_label="productions",
            codename__in=["add_dailyproduction", "view_dailyproduction"],
        )
        self.manager_group.permissions.add(*report_perms)

        self.user = User.objects.create_user(
            username="reporter",
            password="TestPass123",
        )
        self.user.groups.add(self.manager_group)
        Profile.objects.update_or_create(
            user=self.user,
            defaults={
                "oil_company": self.company,
                "department": "Production",
                "phone_number": "+77005554433",
                "bio": "",
            },
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