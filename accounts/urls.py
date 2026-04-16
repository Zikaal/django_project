from django.urls import include, path

from .views import (
    ProfileDetailView,
    RegisterView,
    UserCreateView,
    UserDeleteView,
    UserListView,
    profile_update_view,
    user_update_view,
)

# URL-маршруты приложения accounts.
# Они отвечают за:
# - регистрацию,
# - вход/выход,
# - просмотр и редактирование профиля,
# - CRUD-операции над пользователями для администратора.
urlpatterns = [
    # ===================================================================
    # Маршруты приложения accounts (пользователи и аутентификация)
    # ===================================================================
    # Регистрация нового пользователя.
    # Обычно доступна публично, без роли.
    path(
        "register/",
        RegisterView.as_view(),
        name="register",
    ),
    # Редактирование собственного профиля текущего пользователя.
    # Здесь пользователь меняет только свои данные.
    path(
        "profile/edit/",
        profile_update_view,
        name="profile_edit",
    ),
    # Просмотр своего профиля.
    path(
        "profile/",
        ProfileDetailView.as_view(),
        name="profile",
    ),
    # Список всех пользователей.
    # По бизнес-логике доступен только администраторам.
    path(
        "users/",
        UserListView.as_view(),
        name="user_list",
    ),
    # Создание нового пользователя администратором.
    path(
        "users/create/",
        UserCreateView.as_view(),
        name="user_create",
    ),
    # Редактирование конкретного пользователя по его primary key.
    # Используется функциональное view, потому что там обрабатываются сразу две формы:
    # User и Profile.
    path(
        "users/<int:pk>/edit/",
        user_update_view,
        name="user_update",
    ),
    # Удаление пользователя.
    path(
        "users/<int:pk>/delete/",
        UserDeleteView.as_view(),
        name="user_delete",
    ),
    # ===================================================================
    # Встроенные маршруты Django аутентификации
    # ===================================================================
    #
    # include("django.contrib.auth.urls") подключает готовые пути Django:
    # - /login/
    # - /logout/
    # - /password_change/
    # - /password_change/done/
    # - /password_reset/
    # - /password_reset/done/
    # - /reset/<uidb64>/<token>/
    # - /reset/done/
    #
    # Это удобно, потому что не нужно вручную описывать стандартные auth-маршруты.
    path(
        "",
        include("django.contrib.auth.urls"),
    ),
]
