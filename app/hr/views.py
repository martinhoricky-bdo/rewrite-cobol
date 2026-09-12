"""Design: HR views implement UC-H01 and UC-H02; employee deletion remains forbidden by FK
RESTRICT.
"""

from django.contrib import messages
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.models import Department, Employee
from accounts.permissions import RoleRequiredMixin
from accounts.roles import Role
from core.views import generic
from operations.models import Crew

from .forms import DepartmentForm, EmployeeFilterForm, EmployeeForm
from .services import create_employee


class EmployeeView(RoleRequiredMixin, generic.EditableByMixin):
    """Serves the employee screen for Design employee and department maintenance in UC-H01 and
    UC-H02, applying the access, query, form, and redirect rules configured below.
    """

    model = Employee
    pk_url_kwarg = "empid"
    allowed_roles = (Role.HR, Role.CEO)
    edit_roles = (Role.HR,)


class EmployeeListView(EmployeeView, generic.PageTitleMixin, generic.FilteredListView):
    """Serves the employee list screen for Design employee and department maintenance in UC-H01
    and UC-H02, applying the access, query, form, and redirect rules configured below.
    """

    page_title = "Employees"
    template_name = "hr/employee_list.html"
    filter_form_class = EmployeeFilterForm
    paginate_by = 10

    def filter_queryset(self, queryset, form):
        """Apply validated filter fields to the records displayed by this list screen for employee
        list view.
        """
        return (
            queryset.select_related("dept", "user")
            .name_starts_with(form.value("name", ""))
            .in_department(getattr(form.value("dept"), "pk", None))
        )


class EmployeeDetailView(EmployeeView, generic.PageTitleMixin, DetailView):
    """Serves the employee detail screen for Design employee and department maintenance in
    UC-H01 and UC-H02, applying the access, query, form, and redirect rules configured
    below.
    """

    template_name = "hr/employee_detail.html"
    context_object_name = "employee_record"

    def get_queryset(self):
        """Load the employee relations required by the detail screen."""
        return Employee.objects.select_related("dept", "user")

    def get_page_title(self):
        return f"Employee {self.object.empid}"

    def get_context_data(self, **kwargs):
        """Add the screen-specific display values to the generic template context for employee
        detail view.
        """
        return super().get_context_data(crews=Crew.objects.with_member(self.object), **kwargs)


class EmployeeFormView(
    EmployeeView,
    generic.PageTitleMixin,
    generic.CancelUrlMixin,
    generic.SavedMessageMixin,
):
    """Serves the employee form screen for Design employee and department maintenance in UC-H01
    and UC-H02, applying the access, query, form, and redirect rules configured below.
    """

    allowed_roles = (Role.HR,)
    form_class = EmployeeForm
    template_name = "core/form.html"


class EmployeeCreateView(EmployeeFormView, CreateView):
    """Serves the employee create screen for Design employee and department maintenance in
    UC-H01 and UC-H02, applying the access, query, form, and redirect rules configured
    below.
    """

    page_title = "New employee"

    def form_valid(self, form):
        """Persist validated input and continue with the workflow’s success response for employee
        create view.
        """
        self.object = create_employee(form)
        messages.success(self.request, self.get_saved_message())
        return HttpResponseRedirect(self.get_success_url())


class EmployeeUpdateView(EmployeeFormView, UpdateView):
    """Serves the employee update screen for Design employee and department maintenance in
    UC-H01 and UC-H02, applying the access, query, form, and redirect rules configured
    below.
    """

    def get_page_title(self):
        return f"Edit employee {self.object.empid}"


class DepartmentView(RoleRequiredMixin):
    """Serves the department screen for Design employee and department maintenance in UC-H01
    and UC-H02, applying the access, query, form, and redirect rules configured below.
    """

    allowed_roles = (Role.HR,)
    model = Department


class DepartmentListView(DepartmentView, generic.PageTitleMixin, ListView):
    """Serves the department list screen for Design employee and department maintenance in
    UC-H01 and UC-H02, applying the access, query, form, and redirect rules configured
    below.
    """

    page_title = "Departments"
    template_name = "hr/department_list.html"

    def get_queryset(self):
        """Load managers and employee totals for the department list."""
        return self.model.objects.select_related("manager").annotate(
            employee_count=Count("employees")
        )


class DepartmentUpdateView(
    DepartmentView,
    generic.PageTitleMixin,
    generic.CancelUrlMixin,
    generic.SavedMessageMixin,
    UpdateView,
):
    """Serves the department update screen for Design employee and department maintenance in
    UC-H01 and UC-H02, applying the access, query, form, and redirect rules configured
    below.
    """

    form_class = DepartmentForm
    pk_url_kwarg = "deptid"
    template_name = "core/form.html"
    cancel_url_name = "hr:departments"
    success_url = reverse_lazy("hr:departments")

    def get_page_title(self):
        return f"Edit department {self.object.pk}"
