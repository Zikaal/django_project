from django.contrib import admin
from .models import Profile

admin.site.register(Profile) # Админ теперь может изменять информацию в профиле
