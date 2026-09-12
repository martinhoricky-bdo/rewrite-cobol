"""Admin registrations for employee and department records backed by the legacy DB2 EMPLO
and DEPT tables.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Department, Employee, User

admin.site.register(User, UserAdmin)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Provide DepartmentAdmin behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""

    list_display = ("deptid", "name", "manager")
    search_fields = ("deptid", "name", "manager__empid", "manager__lastname")


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Provide EmployeeAdmin behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""

    list_display = ("empid", "firstname", "lastname", "dept", "email")
    search_fields = ("empid", "firstname", "lastname", "email")
