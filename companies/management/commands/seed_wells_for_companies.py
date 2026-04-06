import random
from decimal import Decimal

from django.core.management.base import BaseCommand

from companies.models import OilCompany
from productions.models import Well


class Command(BaseCommand):
    help = "Создает для каждой компании 1–2 скважины"

    def handle(self, *args, **options):
        well_types = ["мобильная", "стационарная"]
        depths = [3000, 3500, 4200, 4500, 5500]

        companies = OilCompany.objects.all().order_by("id")
        total_created = 0

        if not companies.exists():
            self.stdout.write(self.style.WARNING("Компании не найдены."))
            return

        for company in companies:
            well_count = random.randint(1, 2)

            for i in range(1, well_count + 1):
                well_name = f"COMP{company.id}-WELL-{i:02d}"

                _, created = Well.objects.get_or_create(
                    name=well_name,
                    defaults={
                        "oil_company": company,
                        "type": random.choice(well_types),
                        "max_drilling_depth": random.choice(depths),
                        "latitude": Decimal(str(round(random.uniform(43.0, 47.0), 6))),
                        "longitude": Decimal(str(round(random.uniform(50.0, 58.0), 6))),
                    },
                )

                if created:
                    total_created += 1

        self.stdout.write(self.style.SUCCESS(f"Создано новых скважин: {total_created}"))
        self.stdout.write(self.style.SUCCESS(f"Всего компаний обработано: {companies.count()}"))
