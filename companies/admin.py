from django.contrib import admin
from .models import OilCompany

# Регистрируем модель OilCompany в административной панели Django.
admin.site.register(OilCompany)