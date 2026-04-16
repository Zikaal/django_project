from django.contrib import admin

from .models import OilCompany


@admin.register(OilCompany)
class OilCompanyAdmin(admin.ModelAdmin):
    """
    Настройка админки для модели OilCompany.

    Что дает:
    - удобный список компаний в Django Admin;
    - поиск по названию и региону;
    - фильтрацию по региону;
    - сортировку по названию.
    """

    # Колонки, которые показываются в списке компаний.
    list_display = ("id", "name", "region")

    # Поля, по которым работает строка поиска в admin.
    search_fields = ("name", "region")

    # Боковые фильтры справа в Django Admin.
    list_filter = ("region",)

    # Сортировка списка компаний по умолчанию.
    ordering = ("name",)