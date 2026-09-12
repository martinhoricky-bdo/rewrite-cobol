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
    model = Employee
    pk_url_kwarg = "empid"
    allowed_roles = (Role.HR, Role.CEO)
    edit_roles = (Role.HR,)


class EmployeeListView(EmployeeView, generic.PageTitleMixin, generic.FilteredListView):
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


class EmployeeDetailView(EmployeeView, generic.PageTitleMixin, DetailView):
    template_name = "hr/employee_detail.html"
    context_object_name = "employee_record"

    def get_queryset(self):
        return Employee.objects.select_related("dept", "user")

    def get_page_title(self):
        return f"Employee {self.object.empid}"

    def get_context_data(self, **kwargs):
        return super().get_context_data(crews=Crew.objects.with_member(self.object), **kwargs)


class EmployeeFormView(
    EmployeeView,
    generic.PageTitleMixin,
    generic.CancelUrlMixin,
    generic.SavedMessageMixin,
):
    allowed_roles = (Role.HR,)
    form_class = EmployeeForm
    template_name = "core/form.html"


class EmployeeCreateView(EmployeeFormView, CreateView):
    page_title = "New employee"

    def form_valid(self, form):
        self.object = create_employee(form)
        messages.success(self.request, self.get_saved_message())
        return HttpResponseRedirect(self.get_success_url())


class EmployeeUpdateView(EmployeeFormView, UpdateView):
    def get_page_title(self):
        return f"Edit employee {self.object.empid}"


class DepartmentView(RoleRequiredMixin):
    allowed_roles = (Role.HR,)
    model = Department


class DepartmentListView(DepartmentView, generic.PageTitleMixin, ListView):
    page_title = "Departments"
    template_name = "hr/department_list.html"

    def get_queryset(self):
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
    form_class = DepartmentForm
    pk_url_kwarg = "deptid"
    template_name = "core/form.html"
    cancel_url_name = "hr:departments"
    success_url = reverse_lazy("hr:departments")

    def get_page_title(self):
        return f"Edit department {self.object.pk}"
