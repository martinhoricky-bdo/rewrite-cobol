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
    """Binds the EMPLO table for HR, which may edit, and for the CEO, who only reads."""

    model = Employee
    pk_url_kwarg = "empid"
    allowed_roles = (Role.HR, Role.CEO)
    edit_roles = (Role.HR,)


class EmployeeListView(EmployeeView, generic.PageTitleMixin, generic.FilteredListView):
    """Lists employees with a name, department and initial-letter filter."""

    page_title = "Employees"
    template_name = "hr/employee_list.html"
    filter_form_class = EmployeeFilterForm
    paginate_by = 10

    def filter_queryset(self, queryset, form):
        """Filter employees by the initial letters of the surname and by department."""
        return (
            queryset.select_related("dept", "user")
            .name_starts_with(form.value("name", ""))
            .in_department(getattr(form.value("dept"), "pk", None))
        )


class EmployeeDetailView(EmployeeView, generic.PageTitleMixin, DetailView):
    """Shows one employee together with the crews they belong to."""

    template_name = "hr/employee_detail.html"
    context_object_name = "employee_record"

    def get_queryset(self):
        """Load the employee relations required by the detail screen."""
        return Employee.objects.select_related("dept", "user")

    def get_page_title(self):
        return f"Employee {self.object.empid}"

    def get_context_data(self, **kwargs):
        """Publish the crews the employee serves in."""
        return super().get_context_data(crews=Crew.objects.with_member(self.object), **kwargs)


class EmployeeFormView(
    EmployeeView,
    generic.PageTitleMixin,
    generic.CancelUrlMixin,
    generic.SavedMessageMixin,
):
    """Shared base for the HR employee create and edit forms."""

    allowed_roles = (Role.HR,)
    form_class = EmployeeForm
    template_name = "core/form.html"


class EmployeeCreateView(EmployeeFormView, CreateView):
    """Creates an employee and an inactive account through hr.services.create_employee."""

    page_title = "New employee"

    def form_valid(self, form):
        """Create the employee with an account through the service and confirm it."""
        self.object = create_employee(form)
        messages.success(self.request, self.get_saved_message())
        return HttpResponseRedirect(self.get_success_url())


class EmployeeUpdateView(EmployeeFormView, UpdateView):
    """Edits an employee; EMPID stays unchanged because it is the primary key."""

    def get_page_title(self):
        return f"Edit employee {self.object.empid}"


class DepartmentView(RoleRequiredMixin):
    """Binds the DEPT table for the HR role."""

    allowed_roles = (Role.HR,)
    model = Department


class DepartmentListView(DepartmentView, generic.PageTitleMixin, ListView):
    """Lists departments with their manager and the number of employees."""

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
    """Edits a department; the manager must be one of its own employees."""

    form_class = DepartmentForm
    pk_url_kwarg = "deptid"
    template_name = "core/form.html"
    cancel_url_name = "hr:departments"
    success_url = reverse_lazy("hr:departments")

    def get_page_title(self):
        return f"Edit department {self.object.pk}"
