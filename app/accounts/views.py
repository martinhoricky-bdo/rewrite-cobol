"""Views reconstruct LOGIN (CICS/LOGIN/LOGIN-COB), CRYPTVE verification, and map
LOGINMP/LOGON for UC-A01 through UC-A03.
"""

import logging

from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View

from core.messages import E_AUTH_03

from .forms import LoginForm
from .services import clear_login_failures, login_block_minutes, record_login_failure

logger = logging.getLogger("cobol_airlines.auth")


class AccountLoginView(LoginView):
    """Reconstruct LOGIN (CICS/LOGIN/LOGIN-COB), CRYPTVE verification, and LOGINMP/LOGON
    for UC-A01.
    """

    authentication_form = LoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get(self, request, *args, **kwargs):
        """Implement get behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""
        messages.info(request, "Welcome to COBOL AIRLINES system")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Implement post behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""
        username = request.POST.get("username", "")
        ip_address = request.META.get("REMOTE_ADDR", "unknown")
        if minutes := login_block_minutes(username, ip_address):
            form = self.get_form()
            form.add_error(None, E_AUTH_03.format(minutes=minutes))
            logger.warning("login blocked user=%s ip=%s", username, ip_address)
            return self.form_invalid(form)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        """Implement form_valid behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""
        username = form.cleaned_data["username"]
        ip_address = self.request.META.get("REMOTE_ADDR", "unknown")
        clear_login_failures(username, ip_address)
        logger.info("login success user=%s ip=%s", username, ip_address)
        return super().form_valid(form)

    def form_invalid(self, form):
        """Implement form_invalid behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""
        username = self.request.POST.get("username", "")
        ip_address = self.request.META.get("REMOTE_ADDR", "unknown")
        if self.request.method == "POST" and not login_block_minutes(username, ip_address):
            record_login_failure(username, ip_address)
            logger.warning("login failed user=%s ip=%s", username, ip_address)
        return super().form_invalid(form)


class AccountLogoutView(View):
    """Reconstruct the LOGIN session exit represented by UC-A02."""

    http_method_names = ["get", "post"]

    def dispatch(self, request, *args, **kwargs):
        """Implement dispatch behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""
        username = request.user.get_username() if request.user.is_authenticated else "anonymous"
        logout(request)
        logger.info("logout user=%s", username)
        messages.info(request, "You have been logged out.")
        return redirect("accounts:login")


class AccountPasswordChangeView(PasswordChangeView):
    """Implement UC-A03 password change using the CRYPTVE and CRYPTO-VERIFICATION
    authentication lineage.
    """

    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("core:home")

    def form_valid(self, form):
        """Implement form_valid behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""
        response = super().form_valid(form)
        self.request.user.must_change_password = False
        self.request.user.save(update_fields=["must_change_password"])
        update_session_auth_hash(self.request, self.request.user)
        messages.success(self.request, "Password changed.")
        return response
