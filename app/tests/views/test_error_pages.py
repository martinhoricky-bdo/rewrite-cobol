import pytest
from django.test import RequestFactory

from core.messages import E_AUTH_02
from core.views import server_error
from tests.factories import EmployeeFactory


@pytest.mark.django_db
def test_404_has_explanation_and_home_link(client):
    response = client.get("/does-not-exist/")
    body = response.content.decode()
    assert response.status_code == 404
    assert "The requested page could not be found." in body
    assert 'href="/"' in body


@pytest.mark.django_db
def test_403_page_is_unchanged(client):
    employee = EmployeeFactory(dept__deptid=7, with_user=True)
    client.force_login(employee.user)
    response = client.get("/hr/employees/")
    assert response.status_code == 403
    assert E_AUTH_02 in response.content.decode()
    assert 'href="/"' in response.content.decode()


def test_500_page_renders_without_request_context():
    response = server_error(RequestFactory().get("/broken/"))
    body = response.content.decode()
    assert response.status_code == 500
    assert "Server error" in body
    assert 'href="/"' in body
