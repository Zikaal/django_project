from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from companies.models import OilCompany
from productions.forms import DailyProductionForm
from productions.models import Well, DailyProduction


class DailyProductionUnitTests(TestCase):
    def setUp(self):
        self.company = OilCompany.objects.create(
            name="KazOil",
            region="Atyrau",
        )
        self.well = Well.objects.create(
            name="Well-101",
            oil_company=self.company,
            type="Production",
            max_drilling_depth=3500,
            latitude=Decimal("43.238949"),
            longitude=Decimal("76.889709"),
        )

    def test_calculated_oil_returns_expected_value(self):
        report = DailyProduction(
            well=self.well,
            date=date(2026, 4, 2),
            work_time=Decimal("24.00"),
            liquid_debit=Decimal("100.00"),
            water_cut=Decimal("20.00"),
            oil_density=Decimal("0.85"),
        )

        expected = Decimal("100.00") * (Decimal("1") - Decimal("20.00") / Decimal("100")) * Decimal("0.85")
        self.assertEqual(report.calculated_oil, expected)

    def test_work_time_cannot_be_more_than_24(self):
        report = DailyProduction(
            well=self.well,
            date=date(2026, 4, 2),
            work_time=Decimal("25.00"),
            liquid_debit=Decimal("100.00"),
            water_cut=Decimal("20.00"),
            oil_density=Decimal("0.85"),
        )

        with self.assertRaises(ValidationError) as exc:
            report.full_clean()

        self.assertIn("work_time", exc.exception.message_dict)

    def test_water_cut_cannot_be_more_than_100(self):
        report = DailyProduction(
            well=self.well,
            date=date(2026, 4, 2),
            work_time=Decimal("12.00"),
            liquid_debit=Decimal("100.00"),
            water_cut=Decimal("101.00"),
            oil_density=Decimal("0.85"),
        )

        with self.assertRaises(ValidationError) as exc:
            report.full_clean()

        self.assertIn("water_cut", exc.exception.message_dict)

    def test_daily_production_form_rejects_duplicate_well_and_date(self):
        DailyProduction.objects.create(
            well=self.well,
            date=date(2026, 4, 2),
            work_time=Decimal("12.00"),
            liquid_debit=Decimal("80.00"),
            water_cut=Decimal("15.00"),
            oil_density=Decimal("0.82"),
        )

        form = DailyProductionForm(data={
            "well": self.well.id,
            "date": "2026-04-02",
            "work_time": "10.00",
            "liquid_debit": "70.00",
            "water_cut": "10.00",
            "oil_density": "0.80",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
        self.assertIn("Для этой скважины уже есть запись на эту дату.", form.errors["__all__"])