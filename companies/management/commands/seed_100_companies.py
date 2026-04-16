import random

from django.core.management.base import BaseCommand

from companies.models import OilCompany


class Command(BaseCommand):
    """
    Management command для генерации 100 тестовых нефтяных компаний.

    Используется для:
    - нагрузки на список компаний;
    - проверки пагинации, фильтров, сортировки;
    - подготовки demo/test данных.
    """

    help = "Создает 100 нефтяных компаний"

    def handle(self, *args, **options):
        """
        Создает компании с именами вида:
        - KMG Company 1
        - KMG Company 2
        - ...
        - KMG Company 100

        Если компания уже существует, повторно не создается.
        """
        regions = [
            "Атырауская область",
            "Мангистауская область",
            "Актюбинская область",
            "Кызылординская область",
            "Западно-Казахстанская область",
        ]

        created_count = 0

        for i in range(1, 101):
            company_name = f"KMG Company {i}"

            _, created = OilCompany.objects.get_or_create(
                name=company_name,
                defaults={"region": random.choice(regions)},
            )

            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Создано компаний: {created_count}"))