from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View

from .forms import LoginForm


class AccountLoginView(LoginView):
    authentication_form = LoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get(self, request, *args, **kwargs):
        messages.info(request, "Welcome to COBOL AIRLINES system")
        return super().get(request, *args, **kwargs)


class AccountLogoutView(View):
    http_method_names = ["get", "post"]

    def dispatch(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, "You have been logged out.")
        return redirect("accounts:login")


class AccountPasswordChangeView(PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("core:home")

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.user.must_change_password = False
        self.request.user.save(update_fields=["must_change_password"])
        update_session_auth_hash(self.request, self.request.user)
        messages.success(self.request, "Password changed.")
        return response
