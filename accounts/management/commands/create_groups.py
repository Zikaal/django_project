from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

# Карта ролей и их разрешений.
#
# Структура:
# {
#     "Название_группы": [
#         ("app_label", "permission_codename"),
#         ...
#     ]
# }
#
# Например:
# ("companies", "view_oilcompany") означает permission
# companies.view_oilcompany
ROLE_PERMISSIONS: dict[str, list[tuple[str, str]]] = {
    "Admin": [
        ("companies", "add_oilcompany"),
        ("companies", "change_oilcompany"),
        ("companies", "delete_oilcompany"),
        ("companies", "view_oilcompany"),
        ("productions", "add_well"),
        ("productions", "change_well"),
        ("productions", "delete_well"),
        ("productions", "view_well"),
        ("productions", "add_dailyproduction"),
        ("productions", "change_dailyproduction"),
        ("productions", "delete_dailyproduction"),
        ("productions", "view_dailyproduction"),
        ("accounts", "add_profile"),
        ("accounts", "change_profile"),
        ("accounts", "delete_profile"),
        ("accounts", "view_profile"),
    ],
    "Manager": [
        ("companies", "view_oilcompany"),
        ("productions", "add_well"),
        ("productions", "change_well"),
        ("productions", "delete_well"),
        ("productions", "view_well"),
        ("productions", "add_dailyproduction"),
        ("productions", "change_dailyproduction"),
        ("productions", "delete_dailyproduction"),
        ("productions", "view_dailyproduction"),
        ("accounts", "view_profile"),
    ],
    "Operator": [
        ("companies", "view_oilcompany"),
        ("productions", "view_well"),
        ("productions", "add_dailyproduction"),
        ("productions", "change_dailyproduction"),
        ("productions", "view_dailyproduction"),
    ],
}


class Command(BaseCommand):
    """
    Команда Django management command для создания ролей системы
    и назначения им разрешений.

    Запуск:
        python manage.py create_groups

    Что делает:
    - создает группы Admin, Manager, Operator, если их еще нет;
    - подбирает permissions из базы по app_label и codename;
    - полностью обновляет набор прав у каждой группы.
    """

    help = "Создаёт группы (Admin, Manager, Operator) и назначает им разрешения"

    def handle(self, *args, **options) -> None:
        """
        Основная логика команды.

        Порядок работы:
        1. Проходим по всем ролям из ROLE_PERMISSIONS.
        2. Создаем группу, если ее нет.
        3. Находим все нужные Permission.
        4. Назначаем группе ровно этот список permissions.

        Важно:
        group.permissions.set(...) заменяет права группы целиком,
        а не просто добавляет новые.
        Это удобно, потому что команда становится идемпотентной:
        ее можно запускать повторно для синхронизации ролей.
        """
        for group_name, perm_tuples in ROLE_PERMISSIONS.items():
            # Создаем группу или получаем уже существующую.
            group, _ = Group.objects.get_or_create(name=group_name)

            permissions = []

            for app_label, codename in perm_tuples:
                try:
                    # Ищем Permission по app_label и codename.
                    perm = Permission.objects.get(
                        codename=codename,
                        content_type__app_label=app_label,
                    )
                    permissions.append(perm)
                except Permission.DoesNotExist:
                    # Если permission не найден, команда не падает.
                    # Это защищает от ошибок при неполных миграциях,
                    # но может скрыть проблему конфигурации.
                    pass

            # Полностью синхронизируем список прав группы.
            group.permissions.set(permissions)

        self.stdout.write(self.style.SUCCESS("Группы и разрешения созданы/обновлены."))
