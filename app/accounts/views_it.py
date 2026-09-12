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
    allowed_roles, model, page_title = (Role.IT,), Employee, "Users"
    template_name, filter_form_class, paginate_by = "it/user_list.html", UserFilterForm, 10

    def filter_queryset(self, queryset, form):
        return queryset.select_related("dept", "user").search(form.value("q", "")).order_by("empid")


class AccountActionView(RoleRequiredMixin, SingleObjectMixin, View):
    allowed_roles, model, pk_url_kwarg = (Role.IT,), Employee, "empid"

    def get_queryset(self):
        return Employee.objects.select_related("user")


class ResetPasswordView(AccountActionView):
    def post(self, request, *args, **kwargs):
        employee = self.get_object()
        password = reset_employee_password(employee)
        request.session[PASSWORD_SESSION_KEY] = {"empid": employee.empid, "password": password}
        messages.success(request, f"Password for {employee.empid} reset.")
        return redirect("it:user_password_shown")


class AccountStateView(AccountActionView):
    service = None

    def post(self, request, *args, **kwargs):
        try:
            message = self.service(self.get_object(), request.user)
        except AccountError as error:
            messages.error(request, str(error))
        else:
            messages.success(request, message)
        return redirect("it:users")


class ActivateUserView(AccountStateView):
    service = staticmethod(activate_account)


class DeactivateUserView(AccountStateView):
    service = staticmethod(deactivate_account)


class PasswordShownView(RoleRequiredMixin, TemplateView):
    allowed_roles, template_name = (Role.IT,), "it/user_password_shown.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            temporary=self.request.session.pop(PASSWORD_SESSION_KEY, None), **kwargs
        )
