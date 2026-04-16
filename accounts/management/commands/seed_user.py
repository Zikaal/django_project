from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from accounts.models import Profile
from companies.models import OilCompany

# Получаем активную модель пользователя проекта.
User = get_user_model()


class Command(BaseCommand):
    """
    Команда для быстрого создания первого суперпользователя
    и его профиля.

    Запуск:
        python manage.py seed_user

    Что делает:
    - создает тестовую/стартовую компанию;
    - создает superuser с базовыми данными;
    - создает или обновляет Profile;
    - пытается добавить пользователя в группу Admin.
    """

    help = "Создаёт первого администратора (superuser) и его профиль"

    def handle(self, *args, **options):
        """
        Основной сценарий инициализации первого администратора.
        """

        # Создаем компанию по умолчанию, если ее еще нет.
        # Это удобно, чтобы профиль админа был сразу привязан к компании
        # и приложение имело минимально нужные данные для старта.
        company, _ = OilCompany.objects.get_or_create(
            name="КМГ Главной Офис",
            defaults={"region": "Астана"},
        )

        # Стартовые учетные данные администратора.
        # В реальном production такие значения лучше не хардкодить,
        # а брать из environment variables или аргументов команды.
        email = "admin@example.com"
        username = "admin"
        password = "pass1234"

        # Если такой пользователь уже существует, повторно не создаем.
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"Пользователь {username} уже существует!"))
            return

        # Создаем суперпользователя Django.
        # create_superuser автоматически даст is_staff=True и is_superuser=True.
        user = User.objects.create_superuser(username, email, password)
        user.first_name = "Админ"
        user.last_name = "Системы"
        user.save()

        # Создаем или обновляем профиль администратора.
        Profile.objects.update_or_create(
            user=user,
            defaults={
                "oil_company": company,
                "bio": "Главный системный администратор проекта.",
                "department": "IT Департамент",
                "phone_number": "+7 777 000 00 00",
            },
        )

        # Дополнительно добавляем суперпользователя в группу Admin,
        # если эта группа уже существует.
        #
        # Формально superuser и так имеет полный доступ,
        # но добавление в группу полезно для единообразия логики
        # и корректного отображения роли в интерфейсе/админке.
        admin_group = Group.objects.filter(name="Admin").first()
        if admin_group:
            user.groups.add(admin_group)
            self.stdout.write(self.style.SUCCESS("Пользователь добавлен в группу «Admin»"))
        else:
            self.stdout.write(
                self.style.WARNING("Группа «Admin» не найдена. Запустите: python manage.py create_groups")
            )

        # Итоговое сообщение об успешном создании пользователя.
        self.stdout.write(self.style.SUCCESS(f"Суперпользователь {username} успешно создан! Пароль: {password}"))
