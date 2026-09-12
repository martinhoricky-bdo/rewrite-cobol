from django.urls import path

from . import views_it

urlpatterns = [
    path("users/", views_it.users, name="users"),
    path("users/password/", views_it.user_password_shown, name="user_password_shown"),
    path(
        "users/<str:empid>/reset-password/",
        views_it.user_reset_password,
        name="user_reset_password",
    ),
    path("users/<str:empid>/activate/", views_it.user_activate, name="user_activate"),
    path("users/<str:empid>/deactivate/", views_it.user_deactivate, name="user_deactivate"),
]
