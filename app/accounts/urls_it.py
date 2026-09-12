from django.urls import path

from . import views_it

urlpatterns = [
    path("users/", views_it.UserListView.as_view(), name="users"),
    path("users/password/", views_it.PasswordShownView.as_view(), name="user_password_shown"),
    path(
        "users/<str:empid>/reset-password/",
        views_it.ResetPasswordView.as_view(),
        name="user_reset_password",
    ),
    path("users/<str:empid>/activate/", views_it.ActivateUserView.as_view(), name="user_activate"),
    path(
        "users/<str:empid>/deactivate/",
        views_it.DeactivateUserView.as_view(),
        name="user_deactivate",
    ),
]
