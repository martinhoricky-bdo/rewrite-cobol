import pytest
from django.contrib.messages import get_messages

from core.messages import E_SEL_09
from sales.services import SESSION_KEY
from tests.factories import DepartmentFactory, EmployeeFactory

pytestmark = pytest.mark.django_db


def test_invalid_sale_session_is_removed_and_step_two_reports_expiry(client):
    employee = EmployeeFactory(dept=DepartmentFactory(deptid=7), with_user=True)
    client.force_login(employee.user)
    session = client.session
    session[SESSION_KEY] = {"flight_id": "invalid"}
    session.save()

    response = client.get("/sales/sell/passengers/")

    assert response.status_code == 302
    assert response.url == "/sales/sell/"
    assert SESSION_KEY not in client.session
    assert E_SEL_09 in [str(message) for message in get_messages(response.wsgi_request)]
