import pytest
from django.urls import reverse

from accounts.roles import Role
from hr.forms import MANAGER_DEPARTMENT_ERROR
from tests.factories import DepartmentFactory, EmployeeFactory

pytestmark = pytest.mark.django_db


def test_department_list_and_valid_manager_edit(role_client):
    client = role_client(Role.HR)
    department = DepartmentFactory(deptid=7, name="Sales")
    manager = EmployeeFactory(dept=department)
    response = client.get(reverse("hr:departments"))
    assert response.status_code == 200
    assert "Sales" in response.content.decode()
    response = client.post(
        reverse("hr:department_edit", args=[department.pk]),
        {"name": "Sales team", "manager": manager.pk},
    )
    department.refresh_from_db()
    assert response.status_code == 302
    assert department.manager == manager


def test_manager_from_another_department_is_rejected(role_client):
    client = role_client(Role.HR)
    department = DepartmentFactory(deptid=7)
    outsider = EmployeeFactory(dept=DepartmentFactory(deptid=8))
    response = client.post(
        reverse("hr:department_edit", args=[department.pk]),
        {"name": department.name, "manager": outsider.pk},
    )
    assert response.status_code == 200
    assert MANAGER_DEPARTMENT_ERROR in response.content.decode()


def test_invalid_department_edit_does_not_change_department(role_client):
    client = role_client(Role.HR)
    department = DepartmentFactory(deptid=7, name="Sales")
    outsider = EmployeeFactory(dept=DepartmentFactory(deptid=8))
    original_manager = department.manager

    response = client.post(
        reverse("hr:department_edit", args=[department.pk]),
        {"name": "Changed", "manager": outsider.pk},
    )

    department.refresh_from_db()
    assert response.status_code == 200
    assert MANAGER_DEPARTMENT_ERROR in response.content.decode()
    assert department.name == "Sales"
    assert department.manager == original_manager
