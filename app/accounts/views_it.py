"""Design: IT account maintenance for UC-I01, with accounts created alongside employees in
UC-H01.
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView
from django.views.generic.detail import SingleObjectMixin

from accounts.permissions import RoleRequiredMixin
from accounts.roles import Role
from core.views import generic

from .forms import UserFilterForm
from .models import Employee
from .services import AccountError, activate_account, deactivate_account, reset_employee_password

PASSWORD_SESSION_KEY = "it_temporary_password"


class UserListView(RoleRequiredMixin, generic.PageTitleMixin, generic.FilteredListView):
    """Lists employee accounts with their login state, searchable by name or EMPID."""

    allowed_roles = (Role.IT,)
    model = Employee
    page_title = "Users"
    template_name = "it/user_list.html"
    filter_form_class = UserFilterForm
    paginate_by = 10

    def filter_queryset(self, queryset, form):
        """Search accounts by EMPID or name and order them by EMPID."""
        return queryset.select_related("dept", "user").search(form.value("q", "")).order_by("empid")


class AccountActionView(RoleRequiredMixin, SingleObjectMixin, View):
    """Shared base for the POST-only account actions, loading the employee with its account row."""

    allowed_roles = (Role.IT,)
    model = Employee
    pk_url_kwarg = "empid"

    def get_queryset(self):
        """Load the employee together with the account row the action updates."""
        return Employee.objects.select_related("user")


class ResetPasswordView(AccountActionView):
    """Resets an employee password to a generated one and hands it to the confirmation screen."""

    def post(self, request, *args, **kwargs):
        """Generate a new password, keep it in the session and redirect to the screen showing it."""
        employee = self.get_object()
        password = reset_employee_password(employee)
        request.session[PASSWORD_SESSION_KEY] = {"empid": employee.empid, "password": password}
        messages.success(request, f"Password for {employee.empid} reset.")
        return redirect("it:user_password_shown")


class AccountStateView(AccountActionView):
    """Shared base for activation and deactivation; the concrete view supplies the service."""

    service = None

    def post(self, request, *args, **kwargs):
        """Run the configured account service and report its outcome as a message."""
        try:
            message = self.service(self.get_object(), request.user)
        except AccountError as error:
            messages.error(request, str(error))
        else:
            messages.success(request, message)
        return redirect("it:users")


class ActivateUserView(AccountStateView):
    """Activates the employee account through accounts.services.activate_account."""

    service = staticmethod(activate_account)


class DeactivateUserView(AccountStateView):
    """Deactivates the employee account, refusing the signed-in IT user's own account."""

    service = staticmethod(deactivate_account)


class PasswordShownView(RoleRequiredMixin, TemplateView):
    """Shows the generated password once, reading it from the session left by the reset."""

    allowed_roles = (Role.IT,)
    template_name = "it/user_password_shown.html"

    def get_context_data(self, **kwargs):
        """Take the generated password out of the session so it is displayed only once."""
        return super().get_context_data(
            temporary=self.request.session.pop(PASSWORD_SESSION_KEY, None), **kwargs
        )
