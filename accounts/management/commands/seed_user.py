from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from accounts.models import Profile
from companies.models import OilCompany

User = get_user_model()


class Command(BaseCommand):
    help = "Создаёт первого администратора (superuser) и его профиль"

    def handle(self, *args, **options):
        company, _ = OilCompany.objects.get_or_create(name="КМГ Главной Офис", defaults={"region": "Астана"})

        email = "admin@example.com"
        username = "admin"
        password = "pass1234"

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"Пользователь {username} уже существует!"))
            return

        user = User.objects.create_superuser(username, email, password)
        user.first_name = "Админ"
        user.last_name = "Системы"
        user.save()

        Profile.objects.update_or_create(
            user=user,
            defaults={
                "oil_company": company,
                "bio": "Главный системный администратор проекта.",
                "department": "IT Департамент",
                "phone_number": "+7 777 000 00 00",
            },
        )

        # Добавляем суперпользователя в группу Admin (если она существует)
        admin_group = Group.objects.filter(name="Admin").first()
        if admin_group:
            user.groups.add(admin_group)
            self.stdout.write(self.style.SUCCESS(f"Пользователь добавлен в группу «Admin»"))
        else:
            self.stdout.write(
                self.style.WARNING("Группа «Admin» не найдена. Запустите: python manage.py create_groups")
            )

        self.stdout.write(self.style.SUCCESS(f"Суперпользователь {username} успешно создан! Пароль: {password}"))