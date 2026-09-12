"""Design: employee and department forms implement UC-H01 and UC-H02 with employee deletion
forbidden by FK RESTRICT.
"""

import re
from decimal import Decimal

from django import forms
from django.core.validators import RegexValidator
from django.db.models import Max
from django.utils import timezone

from accounts.models import Department, Employee
from core.forms import FilterForm

FUTURE_ADMISSION_ERROR = "Admission date cannot be in the future."
MANAGER_DEPARTMENT_ERROR = "Manager must belong to this department."


class EmployeeFilterForm(FilterForm):
    """Provide EmployeeFilterForm behavior for Design use cases UC-H01 and UC-H02."""

    name = forms.CharField(required=False, label="Name starts with")
    dept = forms.ModelChoiceField(
        required=False,
        queryset=Department.objects.order_by("deptid"),
        label="Department",
        empty_label="All",
    )


def next_employee_id() -> str:
    """Return the next numeric legacy employee identifier, padded to eight digits."""
    maximum = Employee.objects.aggregate(value=Max("empid"))["value"]
    return f"{int(maximum or '0') + 1:08d}"


class EmployeeForm(forms.ModelForm):
    """Provide EmployeeForm behavior for Design use cases UC-H01 and UC-H02."""

    empid = forms.CharField(
        max_length=8,
        validators=[RegexValidator(r"^\d{8}$", "Employee ID must contain 8 digits.")],
    )

    class Meta:
        """Provide Meta behavior for Design use cases UC-H01 and UC-H02."""

        model = Employee
        fields = (
            "empid",
            "firstname",
            "lastname",
            "addre",
            "city",
            "zipcode",
            "telephone",
            "email",
            "admidate",
            "salary",
            "dept",
        )
        widgets = {"admidate": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["empid"].disabled = True
        elif not self.is_bound:
            self.initial.setdefault("empid", next_employee_id())

    def clean_telephone(self):
        """Implement clean_telephone behavior for Design use cases UC-H01 and UC-H02."""
        telephone = self.cleaned_data["telephone"]
        if not 10 <= len(telephone) <= 20 or not re.fullmatch(r"[\d +\-]+", telephone):
            raise forms.ValidationError(
                "Telephone must be 10–20 characters and contain only digits, spaces, + or -."
            )
        return telephone

    def clean_admidate(self):
        """Implement clean_admidate behavior for Design use cases UC-H01 and UC-H02."""
        admidate = self.cleaned_data["admidate"]
        if admidate > timezone.localdate():
            raise forms.ValidationError(FUTURE_ADMISSION_ERROR)
        return admidate

    def clean_salary(self):
        """Implement clean_salary behavior for Design use cases UC-H01 and UC-H02."""
        salary = self.cleaned_data["salary"]
        if salary < Decimal("0") or salary > Decimal("999999.99"):
            raise forms.ValidationError("Salary must be between 0 and 999999.99.")
        return salary


class DepartmentForm(forms.ModelForm):
    """Provide DepartmentForm behavior for Design use cases UC-H01 and UC-H02."""

    class Meta:
        """Provide Meta behavior for Design use cases UC-H01 and UC-H02."""

        model = Department
        fields = ("name", "manager")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["manager"].queryset = Employee.objects.filter(dept=self.instance)
        self.fields["manager"].error_messages["invalid_choice"] = MANAGER_DEPARTMENT_ERROR

    def clean_manager(self):
        """Implement clean_manager behavior for Design use cases UC-H01 and UC-H02."""
        manager = self.cleaned_data.get("manager")
        if manager and manager.dept_id != self.instance.deptid:
            raise forms.ValidationError(MANAGER_DEPARTMENT_ERROR)
        return manager
