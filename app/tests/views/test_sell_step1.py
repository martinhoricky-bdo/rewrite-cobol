from datetime import date

import pytest
from freezegun import freeze_time

from accounts.roles import Role
from core.messages import E_SEL_01, E_SEL_02, E_SEL_03, E_SEL_04, E_SEL_05, E_SEL_09
from sales.models import Buy
from tests.factories import DepartmentFactory, EmployeeFactory, FlightFactory, PassengerFactory

pytestmark = pytest.mark.django_db


def login_role(client, deptid):
    employee = EmployeeFactory(dept=DepartmentFactory(deptid=deptid), with_user=True)
    client.force_login(employee.user)


def test_get_prefills_query_parameters(client):
    login_role(client, 7)
    response = client.get("/sales/sell/?flightnum=CB1104&date=2026-09-18&clientid=641")
    assert response.status_code == 200
    assert response.context["form"]["flightnum"].value() == "CB1104"
    assert response.context["form"]["flightdate"].value() == "2026-09-18"
    assert response.context["form"]["clientid"].value() == "641"
    assert not response.context["form"].is_bound


@freeze_time("2026-09-11")
def test_valid_post_stores_and_displays_quote(client):
    login_role(client, 7)
    passenger = PassengerFactory(firstname="Ada", lastname="Lovelace")
    FlightFactory(flightnum="CB1104", flightdate=date(2026, 9, 18))
    response = client.post(
        "/sales/sell/",
        {
            "action": "research",
            "clientid": passenger.pk,
            "flightnum": "CB1104",
            "flightdate": "2026-09-18",
            "count": 2,
        },
    )
    html = response.content.decode()
    assert response.status_code == 200
    assert "241.98 EUR" in html
    assert "Ada Lovelace" in html
    assert client.session["sale_quote"]["flightnum"] == "CB1104"


@freeze_time("2026-09-11")
def test_service_error_clears_old_quote(client):
    login_role(client, 7)
    passenger = PassengerFactory()
    session = client.session
    session["sale_quote"] = {"old": "invalid"}
    session.save()
    response = client.post(
        "/sales/sell/",
        {
            "action": "research",
            "clientid": passenger.pk,
            "flightnum": "CB9999",
            "flightdate": "2026-09-18",
            "count": 1,
        },
    )
    assert E_SEL_05 not in response.content.decode()
    assert "This flight does not exist." in response.content.decode()
    assert "sale_quote" not in client.session


def test_step_two_without_quote_redirects_with_message(client):
    login_role(client, 7)
    response = client.get("/sales/sell/passengers/", follow=True)
    assert response.redirect_chain == [("/sales/sell/", 302)]
    assert E_SEL_09 in response.content.decode()


def test_invalid_step_one_reports_all_field_errors_without_writing(role_client):
    client = role_client(Role.SALES)
    before = Buy.objects.count()

    response = client.post(
        "/sales/sell/",
        {
            "action": "research",
            "clientid": "abc",
            "flightnum": "",
            "flightdate": "bad",
            "count": "x",
        },
    )

    content = response.content.decode()
    assert response.status_code == 200
    for message in (E_SEL_01, E_SEL_02, E_SEL_03, E_SEL_04):
        assert message in content
    assert Buy.objects.count() == before
