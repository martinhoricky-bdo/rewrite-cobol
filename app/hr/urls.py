"""Design: HR routes implement UC-H01 and UC-H02; employee deletion remains forbidden by FK
RESTRICT.
"""

from django.urls import path

from . import views

app_name = "hr"
urlpatterns = [
    path("employees/", views.EmployeeListView.as_view(), name="employees"),
    path("employees/new/", views.EmployeeCreateView.as_view(), name="employee_create"),
    path("employees/<str:empid>/", views.EmployeeDetailView.as_view(), name="employee_detail"),
    path("employees/<str:empid>/edit/", views.EmployeeUpdateView.as_view(), name="employee_edit"),
    path("departments/", views.DepartmentListView.as_view(), name="departments"),
    path(
        "departments/<int:deptid>/edit/",
        views.DepartmentUpdateView.as_view(),
        name="department_edit",
    ),
]
