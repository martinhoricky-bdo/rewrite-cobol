from datetime import date

import pytest

from accounts.roles import Role
from core.messages import E_SEL_01, E_SEL_05_ID, E_SEL_09
from sales.models import Buy, Ticket
from sales.services import SESSION_KEY, quote_sale
from tests.factories import DepartmentFactory, EmployeeFactory, FlightFactory, PassengerFactory

pytestmark = pytest.mark.django_db


def login_role(client, deptid):
    employee = EmployeeFactory(dept=DepartmentFactory(deptid=deptid), with_user=True)
    client.force_login(employee.user)
    return employee


def set_quote(client, flight, passenger, count=3):
    quote = quote_sale(
        clientid=passenger.pk,
        flightnum=flight.flightnum,
        flightdate=flight.flightdate,
        count=count,
        today=date.today(),
    )
    session = client.session
    session[SESSION_KEY] = quote.to_session()
    session.save()


def test_without_quote_redirects_with_message(client):
    login_role(client, 7)
    response = client.get("/sales/sell/passengers/", follow=True)
    assert response.redirect_chain == [("/sales/sell/", 302)]
    assert E_SEL_09 in response.content.decode()


def test_get_and_check_names(client):
    login_role(client, 7)
    first, second = PassengerFactory.create_batch(2)
    flight = FlightFactory(flightdate=date.today())
    set_quote(client, flight, first, 3)
    response = client.get("/sales/sell/passengers/")
    assert len(response.context["rows"]) == 3
    assert response.context["form"]["client_1"].value() == first.pk
    response = client.post(
        "/sales/sell/passengers/",
        {"action": "check", "client_1": first.pk, "client_2": second.pk, "client_3": 999999},
    )
    html = response.content.decode()
    assert first.full_name in html and second.full_name in html
    assert E_SEL_05_ID.format(id=999999) in html


def test_confirm_redirects_to_buy_and_clears_quote(client):
    login_role(client, 7)
    passengers = PassengerFactory.create_batch(3)
    flight = FlightFactory(flightdate=date.today())
    set_quote(client, flight, passengers[0])
    response = client.post(
        "/sales/sell/passengers/",
        {"action": "confirm", **{f"client_{i + 1}": p.pk for i, p in enumerate(passengers)}},
        follow=True,
    )
    buy = response.context["buy"]
    assert response.redirect_chain == [(f"/sales/buys/{buy.pk}/", 302)]
    assert f"Sale {buy.pk} completed." in response.content.decode()
    assert response.context["buy"].tickets.count() == 3
    assert SESSION_KEY not in client.session


def test_name_endpoint_return(client):
    first = PassengerFactory(firstname="EDITH", lastname="DWELLY")
    login_role(client, 7)
    assert (
        "EDITH DWELLY"
        in client.get(f"/sales/sell/passenger-name/?clientid={first.pk}").content.decode()
    )
    assert (
        E_SEL_05_ID.format(id=999999)
        in client.get("/sales/sell/passenger-name/?clientid=999999").content.decode()
    )
    flight = FlightFactory(flightdate=date.today())
    set_quote(client, flight, first, 1)
    assert client.post("/sales/sell/passengers/", {"action": "return"}).url == "/sales/sell/"


def test_invalid_step_two_reports_row_error_without_writing(role_client):
    client = role_client(Role.SALES)
    passenger = PassengerFactory()
    flight = FlightFactory(flightdate=date.today())
    set_quote(client, flight, passenger, count=1)
    buys_before = Buy.objects.count()
    tickets_before = Ticket.objects.count()

    response = client.post("/sales/sell/passengers/", {"action": "confirm", "client_1": "abc"})

    assert response.status_code == 200
    assert E_SEL_01 in response.content.decode()
    assert Buy.objects.count() == buys_before
    assert Ticket.objects.count() == tickets_before
