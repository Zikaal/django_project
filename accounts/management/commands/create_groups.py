from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


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
    help = "Создаёт группы (Admin, Manager, Operator) и назначает им разрешения"

    def handle(self, *args, **options) -> None:
        for group_name, perm_tuples in ROLE_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=group_name)

            permissions = []
            for app_label, codename in perm_tuples:
                try:
                    perm = Permission.objects.get(
                        codename=codename,
                        content_type__app_label=app_label,
                    )
                    permissions.append(perm)
                except Permission.DoesNotExist:
                    pass

            group.permissions.set(permissions)

        self.stdout.write(self.style.SUCCESS("Группы и разрешения созданы/обновлены."))