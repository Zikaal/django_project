"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from accounts.views import ProfileUpdateView, RegisterView, UserListView

urlpatterns = [  # Список всех URL-маршрутов проекта
    path("admin/", admin.site.urls),  # Маршрут для встроенной админ-панели Django

    path("accounts/register/", RegisterView.as_view(), name="register"),  # Маршрут страницы регистрации нового пользователя
    path("accounts/profile/", ProfileUpdateView.as_view(), name="profile"),  # Маршрут страницы профиля текущего пользователя
    path("accounts/users/", UserListView.as_view(), name="user_list"),  # Маршрут страницы со списком всех пользователей

    path("accounts/", include("django.contrib.auth.urls")),  # Подключаем встроенные маршруты Django для входа, выхода и работы с паролями
    path("productions/", include("productions.urls")),  # Подключаем маршруты приложения productions для работы со скважинами и суточными рапортами
]