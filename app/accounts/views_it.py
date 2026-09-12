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
    """Serves the user list screen for authentication and IT account workflows in UC-A01–A03
    and UC-I01, applying the access, query, form, and redirect rules configured below.
    """

    allowed_roles = (Role.IT,)
    model = Employee
    page_title = "Users"
    template_name = "it/user_list.html"
    filter_form_class = UserFilterForm
    paginate_by = 10

    def filter_queryset(self, queryset, form):
        """Apply validated filter fields to the records displayed by this list screen for user list
        view.
        """
        return queryset.select_related("dept", "user").search(form.value("q", "")).order_by("empid")


class AccountActionView(RoleRequiredMixin, SingleObjectMixin, View):
    """Serves the account action screen for authentication and IT account workflows in
    UC-A01–A03 and UC-I01, applying the access, query, form, and redirect rules configured
    below.
    """

    allowed_roles = (Role.IT,)
    model = Employee
    pk_url_kwarg = "empid"

    def get_queryset(self):
        """Build the ordered or related queryset required by this screen for account action view."""
        return Employee.objects.select_related("user")


class ResetPasswordView(AccountActionView):
    """Serves the reset password screen for authentication and IT account workflows in
    UC-A01–A03 and UC-I01, applying the access, query, form, and redirect rules configured
    below.
    """

    def post(self, request, *args, **kwargs):
        """Process the submitted account action and redirect with its resulting status message for
        reset password view.
        """
        employee = self.get_object()
        password = reset_employee_password(employee)
        request.session[PASSWORD_SESSION_KEY] = {"empid": employee.empid, "password": password}
        messages.success(request, f"Password for {employee.empid} reset.")
        return redirect("it:user_password_shown")


class AccountStateView(AccountActionView):
    """Serves the account state screen for authentication and IT account workflows in
    UC-A01–A03 and UC-I01, applying the access, query, form, and redirect rules configured
    below.
    """

    service = None

    def post(self, request, *args, **kwargs):
        """Process the submitted account action and redirect with its resulting status message for
        account state view.
        """
        try:
            message = self.service(self.get_object(), request.user)
        except AccountError as error:
            messages.error(request, str(error))
        else:
            messages.success(request, message)
        return redirect("it:users")


class ActivateUserView(AccountStateView):
    """Serves the activate user screen for authentication and IT account workflows in
    UC-A01–A03 and UC-I01, applying the access, query, form, and redirect rules configured
    below.
    """

    service = staticmethod(activate_account)


class DeactivateUserView(AccountStateView):
    """Serves the deactivate user screen for authentication and IT account workflows in
    UC-A01–A03 and UC-I01, applying the access, query, form, and redirect rules configured
    below.
    """

    service = staticmethod(deactivate_account)


class PasswordShownView(RoleRequiredMixin, TemplateView):
    """Serves the password shown screen for authentication and IT account workflows in
    UC-A01–A03 and UC-I01, applying the access, query, form, and redirect rules configured
    below.
    """

    allowed_roles = (Role.IT,)
    template_name = "it/user_password_shown.html"

    def get_context_data(self, **kwargs):
        """Add the screen-specific display values to the generic template context for password
        shown view.
        """
        return super().get_context_data(
            temporary=self.request.session.pop(PASSWORD_SESSION_KEY, None), **kwargs
        )
