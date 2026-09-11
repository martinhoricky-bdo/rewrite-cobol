import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory

from accounts.permissions import role_required
from accounts.roles import Role
from tests.factories import DepartmentFactory, EmployeeFactory, UserFactory

pytestmark = pytest.mark.django_db


@role_required(Role.SALES)
def sales_only(request):
    return HttpResponse("allowed")


def request_for(user):
    request = RequestFactory().get("/sales/")
    request.user = user
    return request


def test_anonymous_is_redirected():
    response = sales_only(request_for(AnonymousUser()))
    assert response.status_code == 302
    assert response.url == "/login/?next=/sales/"


def test_other_role_is_denied():
    employee = EmployeeFactory(dept=DepartmentFactory(deptid=6), with_user=True)
    with pytest.raises(PermissionDenied):
        sales_only(request_for(employee.user))


def test_allowed_role():
    employee = EmployeeFactory(dept=DepartmentFactory(deptid=7), with_user=True)
    assert sales_only(request_for(employee.user)).status_code == 200


def test_superuser_without_employee():
    user = UserFactory(is_superuser=True)
    assert sales_only(request_for(user)).status_code == 200
