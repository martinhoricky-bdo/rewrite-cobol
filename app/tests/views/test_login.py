import pytest
from django.contrib.auth import authenticate

from accounts.roles import ROLE_BY_DEPT
from core.messages import E_AUTH_01
from tests.factories import DepartmentFactory, EmployeeFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_login_success(client):
    user = UserFactory()
    response = client.post(
        "/login/", {"username": user.username, "password": f"pw-{user.username}"}
    )
    assert response.status_code == 302
    assert response.url == "/"


@pytest.mark.parametrize("kind", ["wrong_password", "missing", "inactive"])
def test_login_failures_share_one_message(client, kind):
    username = "10009999"
    password = "invalid-password"
    if kind != "missing":
        UserFactory(username=username, is_active=kind != "inactive")
        if kind == "inactive":
            password = f"pw-{username}"
    response = client.post("/login/", {"username": username, "password": password})
    content = response.content.decode()
    assert response.status_code == 200
    assert content.count(E_AUTH_01) == 1


@pytest.mark.parametrize("deptid", range(1, 10))
def test_role_home_is_not_available(client, deptid):
    department = DepartmentFactory(deptid=deptid)
    employee = EmployeeFactory(dept=department, with_user=True)
    client.force_login(employee.user)
    response = client.get("/")
    if deptid in (5, 6, 7, 9):
        assert response.status_code == 302
        expected = {
            5: "/hr/employees/",
            6: "/it/users/",
            7: "/sales/flights/",
            9: "/schedule/flights/",
        }
        assert response.url == expected[deptid]
        return
    label = ROLE_BY_DEPT[deptid].label
    assert response.status_code == 200
    assert f"The {label} functions are not available yet." in response.content.decode()


def test_logout_ends_session(client):
    user = UserFactory()
    client.force_login(user)
    response = client.get("/logout/")
    assert response.status_code == 302
    assert response.url == "/login/"
    assert "_auth_user_id" not in client.session


def test_password_change(client):
    user = UserFactory()
    old_password = f"pw-{user.username}"
    client.force_login(user)
    response = client.post(
        "/password/",
        {
            "old_password": old_password,
            "new_password1": "new-password-42",
            "new_password2": "new-password-42",
        },
    )
    assert response.status_code == 302
    assert authenticate(username=user.username, password=old_password) is None
    assert authenticate(username=user.username, password="new-password-42") is not None


def test_must_change_password(client):
    user = UserFactory(must_change_password=True)
    client.force_login(user)
    response = client.get("/")
    assert response.status_code == 302
    assert response.url == "/password/"
    response = client.post(
        "/password/",
        {
            "old_password": f"pw-{user.username}",
            "new_password1": "changed-password",
            "new_password2": "changed-password",
        },
    )
    user.refresh_from_db()
    assert response.status_code == 302
    assert user.must_change_password is False
