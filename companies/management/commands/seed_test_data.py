import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import Profile
from companies.models import OilCompany
from productions.models import Well


class Command(BaseCommand):
    """
    Комплексная management command для заполнения проекта тестовыми данными.

    Что создает:
    - несколько нефтяных компаний;
    - пользователей для этих компаний;
    - профили пользователей;
    - скважины для компаний.

    Подходит для:
    - локальной разработки;
    - демо;
    - первичной проверки интерфейса и связей моделей.
    """

    help = "Заполняет проект тестовыми компаниями, пользователями и скважинами"

    def handle(self, *args, **options):
        User = get_user_model()

        # Набор заранее подготовленных компаний.
        companies_data = [
            {"name": "Эмбамунайгас", "region": "Атырауская область", "code": "emb"},
            {"name": "Озенмунайгас", "region": "Мангистауская область", "code": "ozm"},
            {"name": "KMG Drilling & Services", "region": "Астана", "code": "kds"},
            {"name": "Мангистаумунайгаз", "region": "Мангистауская область", "code": "mmg"},
        ]

        # Справочники случайных значений для генерации пользователей.
        first_names = [
            "Азамат", "Нуржан", "Ерлан", "Данияр", "Марат",
            "Алия", "Айгерим", "Жанар", "Инкар", "Асель",
        ]
        last_names = [
            "Нурбеков", "Сериков", "Касымов", "Тлеубаев", "Омаров",
            "Ахметова", "Садыкова", "Ибрагимова", "Жумагалиева", "Каримова",
        ]
        departments = [
            "Геология",
            "Бурение",
            "Добыча",
            "ИТ",
            "Производство",
            "Аналитика",
        ]

        # Справочники для генерации скважин.
        well_types = ["мобильная", "стационарная"]
        depths = [3000, 3500, 4200, 4500, 5500]

        # Пароль для всех новых пользователей.
        # Удобно для dev/demo, но не для production.
        default_password = "Test12345!"

        total_users = 0
        total_wells = 0

        for company_data in companies_data:
            # Создаем компанию или получаем существующую.
            company, created = OilCompany.objects.get_or_create(
                name=company_data["name"],
                defaults={"region": company_data["region"]},
            )

            # Если компания уже была, но регион отличается — обновляем регион.
            if not created and company.region != company_data["region"]:
                company.region = company_data["region"]
                company.save()

            # Для каждой компании случайно генерируем число пользователей и скважин.
            user_count = random.randint(5, 10)
            well_count = random.randint(3, 5)

            # Создаем пользователей компании.
            for i in range(1, user_count + 1):
                username = f"{company_data['code']}_user_{i}"
                email = f"{username}@example.com"

                user, user_created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "email": email,
                        "first_name": random.choice(first_names),
                        "last_name": random.choice(last_names),
                    },
                )

                if user_created:
                    user.set_password(default_password)
                    user.save()
                    total_users += 1

                # Создаем/обновляем профиль пользователя.
                profile, _ = Profile.objects.get_or_create(user=user)
                profile.oil_company = company

                if not profile.department:
                    profile.department = random.choice(departments)

                if not profile.phone_number:
                    profile.phone_number = f"+7701{random.randint(1000000, 9999999)}"

                profile.save()

            # Создаем скважины компании.
            for i in range(1, well_count + 1):
                well_name = f"{company_data['code'].upper()}-{i:03d}"

                _, well_created = Well.objects.get_or_create(
                    name=well_name,
                    defaults={
                        "oil_company": company,
                        "type": random.choice(well_types),
                        "max_drilling_depth": random.choice(depths),
                        "latitude": Decimal(str(round(random.uniform(43.0, 47.0), 6))),
                        "longitude": Decimal(str(round(random.uniform(50.0, 58.0), 6))),
                    },
                )

                if well_created:
                    total_wells += 1

        self.stdout.write(self.style.SUCCESS("Тестовые данные успешно созданы."))
        self.stdout.write(self.style.SUCCESS(f"Новых пользователей создано: {total_users}"))
        self.stdout.write(self.style.SUCCESS(f"Новых скважин создано: {total_wells}"))
        self.stdout.write(
            self.style.WARNING(f"Пароль для всех новых пользователей: {default_password}")
        )