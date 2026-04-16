import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from productions.models import DailyProduction, Well


class Command(BaseCommand):
    """
    Management command для генерации DailyProduction
    для каждой скважины на каждый день 2025 года.

    Полезна для:
    - тестирования аналитики и dashboard;
    - проверки пагинации и фильтрации по датам;
    - наполнения базы большим объемом данных.
    """

    help = "Создает DailyProduction для каждой скважины на каждый день 2025 года"

    def handle(self, *args, **options):
        """
        Проходит по всем скважинам и для каждой даты 2025 года
        создает запись DailyProduction, если ее еще нет.
        """
        start_date = date(2025, 1, 1)
        end_date = date(2025, 12, 31)

        wells = Well.objects.select_related("oil_company").all()
        total_created = 0

        if not wells.exists():
            self.stdout.write(self.style.WARNING("Скважины не найдены."))
            return

        for well in wells:
            current_date = start_date

            while current_date <= end_date:
                _, created = DailyProduction.objects.get_or_create(
                    well=well,
                    date=current_date,
                    defaults={
                        "work_time": Decimal(str(round(random.uniform(12, 24), 2))),
                        "liquid_debit": Decimal(str(round(random.uniform(50, 500), 2))),
                        "water_cut": Decimal(str(round(random.uniform(0, 100), 2))),
                        "oil_density": Decimal(str(round(random.uniform(0.75, 0.95), 3))),
                    },
                )

                if created:
                    total_created += 1

                current_date += timedelta(days=1)

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово. Создано записей DailyProduction: {total_created}"
            )
        )