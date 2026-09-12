from django.urls import path

from . import views

app_name = "hr"

urlpatterns = [
    path("employees/", views.employees, name="employees"),
    path("employees/new/", views.employee_create, name="employee_create"),
    path("employees/<str:empid>/", views.employee_detail, name="employee_detail"),
    path("employees/<str:empid>/edit/", views.employee_edit, name="employee_edit"),
    path("departments/", views.departments, name="departments"),
    path("departments/<int:deptid>/edit/", views.department_edit, name="department_edit"),
]
