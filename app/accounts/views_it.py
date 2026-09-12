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
    """Provide UserListView behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""

    allowed_roles = (Role.IT,)
    model = Employee
    page_title = "Users"
    template_name = "it/user_list.html"
    filter_form_class = UserFilterForm
    paginate_by = 10

    def filter_queryset(self, queryset, form):
        """Implement filter_queryset behavior for the LOGIN, EMPLO, and DEPT legacy
        lineage.
        """
        return queryset.select_related("dept", "user").search(form.value("q", "")).order_by("empid")


class AccountActionView(RoleRequiredMixin, SingleObjectMixin, View):
    """Provide AccountActionView behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""

    allowed_roles = (Role.IT,)
    model = Employee
    pk_url_kwarg = "empid"

    def get_queryset(self):
        """Implement get_queryset behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""
        return Employee.objects.select_related("user")


class ResetPasswordView(AccountActionView):
    """Provide ResetPasswordView behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""

    def post(self, request, *args, **kwargs):
        """Implement post behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""
        employee = self.get_object()
        password = reset_employee_password(employee)
        request.session[PASSWORD_SESSION_KEY] = {"empid": employee.empid, "password": password}
        messages.success(request, f"Password for {employee.empid} reset.")
        return redirect("it:user_password_shown")


class AccountStateView(AccountActionView):
    """Provide AccountStateView behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""

    service = None

    def post(self, request, *args, **kwargs):
        """Implement post behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""
        try:
            message = self.service(self.get_object(), request.user)
        except AccountError as error:
            messages.error(request, str(error))
        else:
            messages.success(request, message)
        return redirect("it:users")


class ActivateUserView(AccountStateView):
    """Provide ActivateUserView behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""

    service = staticmethod(activate_account)


class DeactivateUserView(AccountStateView):
    """Provide DeactivateUserView behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""

    service = staticmethod(deactivate_account)


class PasswordShownView(RoleRequiredMixin, TemplateView):
    """Provide PasswordShownView behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""

    allowed_roles = (Role.IT,)
    template_name = "it/user_password_shown.html"

    def get_context_data(self, **kwargs):
        """Implement get_context_data behavior for the LOGIN, EMPLO, and DEPT legacy
        lineage.
        """
        return super().get_context_data(
            temporary=self.request.session.pop(PASSWORD_SESSION_KEY, None), **kwargs
        )
