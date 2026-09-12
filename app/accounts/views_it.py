from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.permissions import role_required
from accounts.roles import Role

from .models import Employee
from .services import reset_employee_password

PASSWORD_SESSION_KEY = "it_temporary_password"


@role_required(Role.IT)
def users(request):
    query = request.GET.get("q", "").strip()
    employees = Employee.objects.select_related("dept", "user").order_by("empid")
    if query:
        employees = employees.filter(
            Q(firstname__icontains=query)
            | Q(lastname__icontains=query)
            | Q(dept__name__icontains=query)
        )
    page_obj = Paginator(employees, 10).get_page(request.GET.get("page"))
    query_params = request.GET.copy()
    query_params.pop("page", None)
    return render(
        request,
        "it/user_list.html",
        {"page_obj": page_obj, "query": query, "query_params": query_params.urlencode()},
    )


@require_POST
@role_required(Role.IT)
def user_reset_password(request, empid):
    employee = get_object_or_404(Employee.objects.select_related("user"), pk=empid)
    password = reset_employee_password(employee)
    request.session[PASSWORD_SESSION_KEY] = {"empid": employee.empid, "password": password}
    messages.success(request, f"Password for {empid} reset.")
    return redirect("it:user_password_shown")


@role_required(Role.IT)
def user_password_shown(request):
    temporary = request.session.pop(PASSWORD_SESSION_KEY, None)
    return render(request, "it/user_password_shown.html", {"temporary": temporary})


@require_POST
@role_required(Role.IT)
def user_activate(request, empid):
    employee = get_object_or_404(Employee.objects.select_related("user"), pk=empid)
    if employee.user is None:
        messages.error(request, "This employee has no account.")
    else:
        employee.user.is_active = True
        employee.user.save(update_fields=["is_active"])
        messages.success(request, f"Account {empid} activated.")
    return redirect("it:users")


@require_POST
@role_required(Role.IT)
def user_deactivate(request, empid):
    employee = get_object_or_404(Employee.objects.select_related("user"), pk=empid)
    if employee.user_id == request.user.pk:
        messages.error(request, "You cannot deactivate your own account.")
    elif employee.user is None:
        messages.error(request, "This employee has no account.")
    else:
        employee.user.is_active = False
        employee.user.save(update_fields=["is_active"])
        messages.success(request, f"Account {empid} deactivated.")
    return redirect("it:users")
