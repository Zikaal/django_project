from django.contrib import admin
from .models import Well, DailyProduction

admin.site.register(Well)  # Регистрируем модель Well в админке, чтобы можно было управлять скважинами через /admin
admin.site.register(DailyProduction)  # Регистрируем модель DailyProduction в админке, чтобы можно было управлять суточными рапортами через /admin