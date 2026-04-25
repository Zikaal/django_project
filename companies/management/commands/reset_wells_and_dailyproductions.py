from django.core.management.base import BaseCommand

from productions.models import DailyProduction, Well


class Command(BaseCommand):
    """
    Management command для полной очистки таблиц:
    - Well
    - DailyProduction

    Полезна для:
    - повторного наполнения базы тестовыми данными;
    - сброса демо-окружения;
    - локальной разработки.
    """

    help = "Удаляет все скважины и все суточные рапорты"

    def handle(self, *args, **options):
        """
        Сначала считаем, сколько объектов будет удалено,
        затем удаляем все записи и выводим итоговую статистику.
        """
        daily_count = DailyProduction.objects.count()
        well_count = Well.objects.count()

        # Сначала удаляем зависимые данные, затем скважины.
        DailyProduction.objects.all().delete()
        Well.objects.all().delete()

        self.stdout.write(self.style.SUCCESS(f"Удалено DailyProduction: {daily_count}, удалено Well: {well_count}"))
