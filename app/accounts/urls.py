"""Routes for LOGIN (CICS/LOGIN/LOGIN-COB), CRYPTVE password verification, and UC-A01
through UC-A03.
"""

from django.urls import path

from .views import AccountLoginView, AccountLogoutView, AccountPasswordChangeView

app_name = "accounts"

urlpatterns = [
    path("login/", AccountLoginView.as_view(), name="login"),
    path("logout/", AccountLogoutView.as_view(), name="logout"),
    path("password/", AccountPasswordChangeView.as_view(), name="password_change"),
]
