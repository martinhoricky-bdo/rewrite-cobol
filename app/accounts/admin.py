from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Department, Employee, User

admin.site.register(User, UserAdmin)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("deptid", "name", "manager")
    search_fields = ("deptid", "name", "manager__empid", "manager__lastname")


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("empid", "firstname", "lastname", "dept", "email")
    search_fields = ("empid", "firstname", "lastname", "email")
