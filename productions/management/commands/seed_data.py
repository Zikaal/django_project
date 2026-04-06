import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from accounts.models import Profile
from companies.models import OilCompany
from productions.models import DailyProduction, Well

User = get_user_model()


class Command(BaseCommand):
    help = "Запуск генератора большого объема тестовых данных (seed) по аналогии с Задача 3 (php_project)"

    def handle(self, *args, **options):
        fake = Faker("ru_RU")

        self.stdout.write("Создание 22 нефтяных компаний...")
        companies = []
        for _ in range(22):
            # Используем get_or_create для гарантии уникальности или просто create
            company_name = f"{fake.company()} - {fake.unique.random_number(digits=5)}"
            company, _ = OilCompany.objects.get_or_create(name=company_name, defaults={"region": fake.city()})
            companies.append(company)

        self.stdout.write(f"Создано {len(companies)} компаний.")

        well_types = ["Добывающая", "Нагнетательная", "Оценочная", "Разведочная"]
        departments = ["Добыча", "Бурение", "Геология", "ИТ", "Финансы"]

        # Первые X компаний, для которых будем генерировать полную историю (2025 год)
        full_history_companies_count = random.randint(3, 5)

        total_users = 0
        total_wells = 0
        reports_batch = []
        end_date = timezone.now().date()

        self.stdout.write("Генерация сотрудников, скважин и статистики...")

        default_password = make_password("password")

        for company_index, company in enumerate(companies):
            # 1. Для каждой компании генерируем 2-5 сотрудников
            num_users = random.randint(2, 5)
            for _ in range(num_users):
                username = f"{fake.unique.user_name()}_{random.randint(1000, 99999)}"
                user = User.objects.create(
                    username=username,
                    email=fake.email(),
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    password=default_password,
                )
                Profile.objects.update_or_create(
                    user=user,
                    defaults={
                        "oil_company": company,
                        "bio": fake.text(max_nb_chars=100),
                        "department": random.choice(departments),
                        "phone_number": fake.phone_number(),
                    },
                )
                total_users += 1

            # 2. Для каждой компании генерируем 2-10 скважин
            num_wells = random.randint(2, 10)
            company_wells = []
            for _ in range(num_wells):
                well = Well.objects.create(
                    name=f"Скв-{fake.unique.random_number(digits=5)}",
                    oil_company=company,
                    type=random.choice(well_types),
                    max_drilling_depth=random.randint(1500, 4500),
                    latitude=Decimal(str(fake.latitude())),
                    longitude=Decimal(str(fake.longitude())),
                )
                company_wells.append(well)
                total_wells += 1

            # 3. Генерация ежедневных показателей только для первых 3-5 компаний
            if company_index < full_history_companies_count:
                # Берем первые 5 скважин из этой компании (сортируя по ID)
                selected_wells = sorted(company_wells, key=lambda w: w.id)[:5]

                for well in selected_wells:
                    for days_ago in range(365):
                        report_date = end_date - timedelta(days=days_ago)
                        reports_batch.append(
                            DailyProduction(
                                well=well,
                                date=report_date,
                                work_time=Decimal(str(random.uniform(20.0, 24.0))).quantize(Decimal("0.00")),
                                liquid_debit=Decimal(str(random.uniform(10.0, 150.0))).quantize(Decimal("0.00")),
                                water_cut=Decimal(str(random.uniform(5.0, 95.0))).quantize(Decimal("0.00")),
                                oil_density=Decimal(str(random.uniform(0.8, 0.95))).quantize(Decimal("0.000")),
                            )
                        )

        self.stdout.write("Массовая вставка рапортов в базу...")
        if reports_batch:
            # Частичная вставка по 1000 записей (предотвращает нехватку памяти)
            chunk_size = 1000
            for i in range(0, len(reports_batch), chunk_size):
                chunk = reports_batch[i : i + chunk_size]
                DailyProduction.objects.bulk_create(chunk, ignore_conflicts=True)

        self.stdout.write(
            self.style.SUCCESS(
                f"Завершено! Компаний: 22, Сотрудников: {total_users}, Скважин: {total_wells}, Рапортов: {len(reports_batch)}."
            )
        )
