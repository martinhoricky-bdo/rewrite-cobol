from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import Department, Employee
from accounts.permissions import current_role, role_required
from accounts.roles import Role
from accounts.services import ensure_user_for_employee
from operations.models import Crew

from .forms import DepartmentForm, EmployeeForm


@role_required(Role.HR, Role.CEO)
def employees(request):
    name = request.GET.get("name", "").strip()
    dept = request.GET.get("dept", "").strip()
    queryset = Employee.objects.select_related("dept", "user").order_by("empid")
    if name:
        queryset = queryset.filter(Q(firstname__istartswith=name) | Q(lastname__istartswith=name))
    if dept:
        queryset = queryset.filter(dept_id=dept)
    page_obj = Paginator(queryset, 10).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(
        request,
        "hr/employee_list.html",
        {
            "page_obj": page_obj,
            "departments": Department.objects.order_by("deptid"),
            "name": name,
            "selected_dept": dept,
            "query_params": params.urlencode(),
            "can_edit": current_role(request.user) == Role.HR,
        },
    )


@role_required(Role.HR, Role.CEO)
def employee_detail(request, empid):
    employee = get_object_or_404(Employee.objects.select_related("dept", "user"), pk=empid)
    crews = Crew.objects.filter(
        Q(commander=employee)
        | Q(copilote=employee)
        | Q(fachief=employee)
        | Q(fliattendant1=employee)
        | Q(fliattendant2=employee)
        | Q(fliattendant3=employee)
    ).distinct()
    return render(
        request,
        "hr/employee_detail.html",
        {
            "employee_record": employee,
            "crews": crews,
            "can_edit": current_role(request.user) == Role.HR,
        },
    )


@role_required(Role.HR)
def employee_create(request):
    form = EmployeeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            employee = form.save()
            ensure_user_for_employee(employee)
        messages.success(request, f"Employee {employee.empid} saved.")
        return redirect("hr:employee_detail", empid=employee.empid)
    return render(request, "hr/employee_form.html", {"form": form, "heading": "New employee"})


@role_required(Role.HR)
def employee_edit(request, empid):
    employee = get_object_or_404(Employee, pk=empid)
    form = EmployeeForm(request.POST or None, instance=employee)
    if request.method == "POST" and form.is_valid():
        employee = form.save()
        messages.success(request, f"Employee {employee.empid} saved.")
        return redirect("hr:employee_detail", empid=employee.empid)
    return render(request, "hr/employee_form.html", {"form": form, "heading": "Edit employee"})


@role_required(Role.HR)
def departments(request):
    queryset = Department.objects.select_related("manager").annotate(
        employee_count=Count("employees")
    )
    return render(request, "hr/department_list.html", {"departments": queryset})


@role_required(Role.HR)
def department_edit(request, deptid):
    department = get_object_or_404(Department, pk=deptid)
    form = DepartmentForm(request.POST or None, instance=department)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Department {department.deptid} saved.")
        return redirect("hr:departments")
    return render(request, "hr/department_form.html", {"form": form, "department": department})
