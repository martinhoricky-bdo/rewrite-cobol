import pytest
from django.urls import reverse

from accounts.models import User
from accounts.roles import Role
from tests.factories import DepartmentFactory, EmployeeFactory
from tests.unit.test_employee_form import employee_data

pytestmark = pytest.mark.django_db


def test_list_filter_and_pagination(role_client):
    client = role_client(Role.HR)
    sales = DepartmentFactory(deptid=7, name="Sales")
    EmployeeFactory(firstname="Alice", dept=sales)
    EmployeeFactory(firstname="Bob", dept=sales)
    for _ in range(9):
        EmployeeFactory(dept=sales)
    response = client.get(reverse("hr:employees"), {"name": "ali", "dept": sales.pk})
    assert response.status_code == 200
    assert response.context["page_obj"].paginator.count == 1
    assert "Alice" in response.content.decode()
    response = client.get(reverse("hr:employees"))
    assert len(response.context["page_obj"]) == 10
    assert response.context["page_obj"].paginator.num_pages == 2
    response = client.get(reverse("hr:employees"), {"dept": "abc"})
    assert response.status_code == 200
    assert response.context["page_obj"].paginator.count == 12


def test_detail_and_edit_preserves_empid(role_client):
    client = role_client(Role.HR)
    employee = EmployeeFactory(empid="10000040", dept=DepartmentFactory(deptid=4))
    assert client.get(reverse("hr:employee_detail", args=[employee.pk])).status_code == 200
    data = employee_data(employee.dept, empid="99999999", firstname="Grace")
    response = client.post(reverse("hr:employee_edit", args=[employee.pk]), data)
    employee.refresh_from_db()
    assert response.status_code == 302
    assert employee.empid == "10000040"
    assert employee.firstname == "Grace"


def test_create_makes_inactive_unusable_account(role_client):
    client = role_client(Role.HR)
    department = DepartmentFactory(deptid=4)
    response = client.post(reverse("hr:employee_create"), employee_data(department))
    user = User.objects.get(username="10000040")
    assert response.status_code == 302
    assert not user.is_active
    assert not user.has_usable_password()
    assert user.employee.empid == "10000040"
