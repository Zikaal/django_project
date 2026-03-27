from django.urls import path, include

from .views import (
    RegisterView,
    UserListView,
    UserCreateView,
    UserDeleteView,
    ProfileDetailView,
    user_update_view,
    profile_update_view
)


urlpatterns = [
    # ===================================================================
    # Маршруты приложения accounts (пользователи и аутентификация)
    # ===================================================================

    # Регистрация нового пользователя
    path(
        "register/",
        RegisterView.as_view(),
        name="register",
    ),

    # Редактирование собственного профиля текущего пользователя
    path(
        "profile/edit/",
        profile_update_view,
        name="profile_edit",
    ),

    # Детали профиля текущего пользователя
    path(
        "profile/", 
        ProfileDetailView.as_view(), 
        name="profile"),

    # Список всех пользователей (для администраторов)
    path(
        "users/",
        UserListView.as_view(),
        name="user_list",
    ),

    # Создание нового пользователя администратором
    path(
        "users/create/",
        UserCreateView.as_view(),
        name="user_create",
    ),

    # Редактирование пользователя и его профиля (функциональное представление)
    path(
        "users/<int:pk>/edit/",
        user_update_view,
        name="user_update",
    ),

    # Удаление пользователя
    path(
        "users/<int:pk>/delete/",
        UserDeleteView.as_view(),
        name="user_delete",
    ),

    # ===================================================================
    # Встроенные маршруты Django аутентификации
    # (login, logout, password_change, password_reset и т.д.)
    # ===================================================================
    path(
        "",
        include("django.contrib.auth.urls"),
    ),
]