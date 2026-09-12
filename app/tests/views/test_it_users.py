import re

import pytest
from django.urls import reverse

from tests.factories import DepartmentFactory, EmployeeFactory, UserFactory

pytestmark = pytest.mark.django_db


def login_as(client, deptid):
    user = UserFactory()
    employee = EmployeeFactory(user=user, dept=DepartmentFactory(deptid=deptid))
    client.force_login(user)
    return employee


def test_user_list_status_filter_and_permissions(client):
    login_as(client, 6)
    EmployeeFactory(firstname="Ada", dept=DepartmentFactory(deptid=7), user=None)
    inactive = UserFactory(is_active=False)
    EmployeeFactory(firstname="Inactive", dept=DepartmentFactory(deptid=7), user=inactive)

    response = client.get(reverse("it:users"), {"q": "Ada"})

    assert response.status_code == 200
    assert "Ada" in response.content.decode()
    assert "no account" in response.content.decode()
    client.logout()
    login_as(client, 7)
    assert client.get(reverse("it:users")).status_code == 403


def test_reset_creates_account_and_password_is_shown_once(client):
    login_as(client, 6)
    employee = EmployeeFactory(user=None)

    response = client.post(reverse("it:user_reset_password", args=[employee.pk]), follow=True)
    content = response.content.decode()
    password = re.search(r"<code>([^<]+)</code>", content).group(1)
    employee.refresh_from_db()

    assert len(password) == 12
    assert employee.user.check_password(password)
    assert employee.user.must_change_password
    assert password not in client.get(reverse("it:user_password_shown")).content.decode()


def test_deactivate_and_refuse_self_deactivation(client):
    admin = login_as(client, 6)
    target = EmployeeFactory(with_user=True, dept=DepartmentFactory(deptid=7))
    client.post(reverse("it:user_deactivate", args=[target.pk]))
    target.user.refresh_from_db()
    assert not target.user.is_active

    response = client.post(reverse("it:user_deactivate", args=[admin.pk]), follow=True)
    admin.user.refresh_from_db()
    assert admin.user.is_active
    assert "You cannot deactivate your own account." in response.content.decode()
