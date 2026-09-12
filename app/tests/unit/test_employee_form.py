from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from hr.forms import FUTURE_ADMISSION_ERROR, EmployeeForm, next_employee_id
from tests.factories import DepartmentFactory, EmployeeFactory

pytestmark = pytest.mark.django_db


def employee_data(department, **overrides):
    data = {
        "empid": "10000040",
        "firstname": "Ada",
        "lastname": "Lovelace",
        "addre": "1 Main Street",
        "city": "Paris",
        "zipcode": "75001",
        "telephone": "+33 123456789",
        "email": "ada@example.com",
        "admidate": timezone.localdate(),
        "salary": "12345.67",
        "dept": department.pk,
    }
    data.update(overrides)
    return data


def test_empid_format_duplicate_and_suggestion():
    department = DepartmentFactory()
    EmployeeFactory(empid="10000039", dept=department)

    assert next_employee_id() == "10000040"
    assert EmployeeForm().initial["empid"] == "10000040"
    form = EmployeeForm(employee_data(department, empid="ABC"))
    assert not form.is_valid()
    assert "8 digits" in form.errors["empid"][0]
    duplicate = EmployeeForm(employee_data(department, empid="10000039"))
    assert not duplicate.is_valid()
    assert "already exists" in duplicate.errors["empid"][0]


def test_future_admission_date_is_rejected():
    department = DepartmentFactory()
    form = EmployeeForm(
        employee_data(department, admidate=timezone.localdate() + timedelta(days=1))
    )
    assert not form.is_valid()
    assert form.errors["admidate"] == [FUTURE_ADMISSION_ERROR]


@pytest.mark.parametrize("telephone", ["123", "123456789x", "+33 12345678901234567890"])
def test_invalid_telephone(telephone):
    form = EmployeeForm(employee_data(DepartmentFactory(), telephone=telephone))
    assert not form.is_valid()
    assert form.errors["telephone"]


@pytest.mark.parametrize("salary", [Decimal("-0.01"), Decimal("1000000.00")])
def test_salary_outside_range(salary):
    form = EmployeeForm(employee_data(DepartmentFactory(), salary=salary))
    assert not form.is_valid()
    assert form.errors["salary"]
