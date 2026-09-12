import re

import pytest
from django.contrib.auth import authenticate
from django.urls import reverse

from accounts.roles import Role
from core.messages import E_AUTH_01
from tests.factories import DepartmentFactory, EmployeeFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_user_list_status_filter(role_client):
    client = role_client(Role.IT)
    EmployeeFactory(firstname="Ada", dept=DepartmentFactory(deptid=7), user=None)
    inactive = UserFactory(is_active=False)
    EmployeeFactory(firstname="Inactive", dept=DepartmentFactory(deptid=7), user=inactive)

    response = client.get(reverse("it:users"), {"q": "Ada"})

    assert response.status_code == 200
    assert "Ada" in response.content.decode()
    assert "no account" in response.content.decode()


def test_reset_creates_account_and_password_is_shown_once(role_client):
    client = role_client(Role.IT)
    employee = EmployeeFactory(user=None)

    response = client.post(reverse("it:user_reset_password", args=[employee.pk]), follow=True)
    content = response.content.decode()
    password = re.search(r"<code>([^<]+)</code>", content).group(1)
    employee.refresh_from_db()

    assert len(password) == 12
    assert employee.user.check_password(password)
    assert employee.user.must_change_password
    assert password not in client.get(reverse("it:user_password_shown")).content.decode()


def test_reset_password_requires_change_after_login(role_client):
    client = role_client(Role.IT)
    target = EmployeeFactory(with_user=True, dept=DepartmentFactory(deptid=7))
    old_password = f"pw-{target.user.username}"

    response = client.post(reverse("it:user_reset_password", args=[target.pk]), follow=True)
    password = re.search(r"<code>([^<]+)</code>", response.content.decode()).group(1)

    assert authenticate(username=target.user.username, password=old_password) is None
    assert authenticate(username=target.user.username, password=password) is not None

    client.logout()
    response = client.post(
        reverse("accounts:login"),
        {"username": target.user.username, "password": password},
        follow=True,
    )
    assert response.status_code == 200
    assert response.redirect_chain[-1] == ("/password/", 302)

    response = client.post(
        reverse("accounts:password_change"),
        {
            "old_password": password,
            "new_password1": "changed-password-42",
            "new_password2": "changed-password-42",
        },
    )
    target.user.refresh_from_db()
    assert response.status_code == 302
    assert target.user.must_change_password is False


def test_deactivate_and_refuse_self_deactivation(client, employee_of):
    admin = employee_of(Role.IT)
    client.force_login(admin.user)
    target = EmployeeFactory(with_user=True, dept=DepartmentFactory(deptid=7))
    client.post(reverse("it:user_deactivate", args=[target.pk]))
    target.user.refresh_from_db()
    assert not target.user.is_active

    response = client.post(reverse("it:user_deactivate", args=[admin.pk]), follow=True)
    admin.user.refresh_from_db()
    assert admin.user.is_active
    assert "You cannot deactivate your own account." in response.content.decode()


def test_deactivated_user_cannot_log_in(role_client):
    client = role_client(Role.IT)
    target = EmployeeFactory(with_user=True, dept=DepartmentFactory(deptid=7))
    password = f"pw-{target.user.username}"

    client.post(reverse("it:user_deactivate", args=[target.pk]))
    client.logout()
    response = client.post(
        reverse("accounts:login"),
        {"username": target.user.username, "password": password},
    )

    assert response.status_code == 200
    assert response.content.decode().count(E_AUTH_01) == 1


def test_user_list_no_password_status_and_pagination(role_client):
    client = role_client(Role.IT)
    no_password = UserFactory()
    no_password.set_unusable_password()
    no_password.save(update_fields=["password"])
    department = DepartmentFactory(deptid=7)
    EmployeeFactory(user=no_password, dept=department)
    for _ in range(9):
        EmployeeFactory(dept=department)

    response = client.get(reverse("it:users"))

    assert response.status_code == 200
    assert len(response.context["page_obj"]) == 10
    assert response.context["page_obj"].paginator.count == 11
    assert "no password" in response.content.decode()

    response = client.get(reverse("it:users"), {"page": 2})
    assert response.status_code == 200
    assert len(response.context["page_obj"]) == 1
