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


class EmployeeView:
    model = Employee
    pk_url_kwarg = "empid"


class EmployeeListView(
    EmployeeView,
    RoleRequiredMixin,
    generic.EditableByMixin,
    generic.PageTitleMixin,
    generic.FilteredListView,
):
    allowed_roles = (Role.HR, Role.CEO)
    edit_roles = (Role.HR,)
    page_title = "Employees"
    template_name = "hr/employee_list.html"
    filter_form_class = EmployeeFilterForm
    paginate_by = 10

    def filter_queryset(self, queryset, form):
        return (
            queryset.select_related("dept", "user")
            .name_starts_with(form.value("name", ""))
            .in_department(getattr(form.value("dept"), "pk", None))
        )


class EmployeeDetailView(
    EmployeeView, RoleRequiredMixin, generic.EditableByMixin, generic.PageTitleMixin, DetailView
):
    allowed_roles = (Role.HR, Role.CEO)
    edit_roles = (Role.HR,)
    template_name = "hr/employee_detail.html"
    context_object_name = "employee_record"

    def get_page_title(self):
        return f"Employee {self.object.empid}"

    def get_queryset(self):
        return Employee.objects.select_related("dept", "user")

    def get_context_data(self, **kwargs):
        return super().get_context_data(crews=Crew.objects.with_member(self.object), **kwargs)


class EmployeeFormView(
    EmployeeView,
    RoleRequiredMixin,
    generic.PageTitleMixin,
    generic.CancelUrlMixin,
    generic.SavedMessageMixin,
):
    allowed_roles = (Role.HR,)
    form_class = EmployeeForm
    template_name = "core/form.html"

    def get_success_url(self):
        return reverse_lazy("hr:employee_detail", kwargs={"empid": self.object.empid})


class EmployeeCreateView(EmployeeFormView, CreateView):
    page_title = "New employee"

    def form_valid(self, form):
        self.object = create_employee(form)
        messages.success(self.request, f"Employee {self.object.pk} saved.")
        return HttpResponseRedirect(self.get_success_url())


class EmployeeUpdateView(EmployeeFormView, UpdateView):
    def get_page_title(self):
        return f"Edit employee {self.object.empid}"


class DepartmentListView(RoleRequiredMixin, generic.PageTitleMixin, ListView):
    allowed_roles = (Role.HR,)
    model = Department
    page_title = "Departments"
    template_name = "hr/department_list.html"

    def get_queryset(self):
        return Department.objects.select_related("manager").annotate(
            employee_count=Count("employees")
        )


class DepartmentUpdateView(
    RoleRequiredMixin,
    generic.PageTitleMixin,
    generic.CancelUrlMixin,
    generic.SavedMessageMixin,
    UpdateView,
):
    allowed_roles = (Role.HR,)
    model = Department
    form_class = DepartmentForm
    pk_url_kwarg = "deptid"
    template_name = "core/form.html"
    cancel_url_name = "hr:departments"
    success_url = reverse_lazy("hr:departments")

    def get_page_title(self):
        return f"Edit department {self.object.pk}"
