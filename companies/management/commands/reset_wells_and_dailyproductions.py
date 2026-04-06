from django.core.management.base import BaseCommand

from productions.models import DailyProduction, Well


class Command(BaseCommand):
    help = "Удаляет все скважины и все суточные рапорты"

    def handle(self, *args, **options):
        daily_count = DailyProduction.objects.count()
        well_count = Well.objects.count()

        DailyProduction.objects.all().delete()
        Well.objects.all().delete()

        self.stdout.write(self.style.SUCCESS(f"Удалено DailyProduction: {daily_count}, удалено Well: {well_count}"))
