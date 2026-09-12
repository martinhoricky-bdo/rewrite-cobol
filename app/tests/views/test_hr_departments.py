import pytest
from django.urls import reverse

from hr.forms import MANAGER_DEPARTMENT_ERROR
from tests.factories import DepartmentFactory, EmployeeFactory, UserFactory

pytestmark = pytest.mark.django_db


def login_as(client, deptid):
    user = UserFactory()
    EmployeeFactory(user=user, dept=DepartmentFactory(deptid=deptid))
    client.force_login(user)


def test_department_list_and_valid_manager_edit(client):
    login_as(client, 5)
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


def test_manager_from_another_department_is_rejected(client):
    login_as(client, 5)
    department = DepartmentFactory(deptid=7)
    outsider = EmployeeFactory(dept=DepartmentFactory(deptid=8))
    response = client.post(
        reverse("hr:department_edit", args=[department.pk]),
        {"name": department.name, "manager": outsider.pk},
    )
    assert response.status_code == 200
    assert MANAGER_DEPARTMENT_ERROR in response.content.decode()


def test_foreign_role_forbidden_for_every_department_url(client):
    department = DepartmentFactory(deptid=7)
    login_as(client, 7)
    assert client.get(reverse("hr:departments")).status_code == 403
    url = reverse("hr:department_edit", args=[department.pk])
    assert client.get(url).status_code == 403
    assert client.post(url, {}).status_code == 403
