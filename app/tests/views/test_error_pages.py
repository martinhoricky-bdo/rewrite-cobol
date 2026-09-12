import pytest
from django.contrib.auth.models import AnonymousUser
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


def test_not_found_exposes_its_safe_message():
    from core.exceptions import NotFound
    from core.views import page_not_found

    request = RequestFactory().get("/missing/")
    request.user = AnonymousUser()
    response = page_not_found(request, NotFound("Safe detail"))

    assert response.status_code == 404
    assert "Safe detail" in response.content.decode()


def test_http404_does_not_expose_internal_message():
    from django.http import Http404

    from core.views import page_not_found

    request = RequestFactory().get("/missing/")
    request.user = AnonymousUser()
    response = page_not_found(request, Http404("Internal detail"))

    assert response.status_code == 404
    assert "Internal detail" not in response.content.decode()
