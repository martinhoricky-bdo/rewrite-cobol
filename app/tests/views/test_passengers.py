import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from accounts.roles import Role
from sales.models import Passenger
from sales.services import PASSENGER_EMAIL_WARNING
from tests.factories import DepartmentFactory, EmployeeFactory, PassengerFactory, TicketFactory

pytestmark = pytest.mark.django_db


def login_role(client, deptid=7):
    employee = EmployeeFactory(dept=DepartmentFactory(deptid=deptid), with_user=True)
    client.force_login(employee.user)
    return employee


def passenger_data(**overrides):
    data = {
        "firstname": "Jean",
        "lastname": "Martin",
        "address": "1 Rue de Paris",
        "city": "Paris",
        "country": "France",
        "zipcode": "75001",
        "telephone": "+33 1 23 45 67 89",
        "email": "jean.martin@example.com",
    }
    data.update(overrides)
    return data


def test_list_is_paginated_and_filtered(client):
    login_role(client)
    match = PassengerFactory(lastname="Duprat")
    for index in range(11):
        PassengerFactory(lastname=f"Martin{index:02d}")
    response = client.get("/sales/passengers/")
    assert len(response.context["page_obj"]) == 10
    assert "page=2" in response.content.decode()
    response = client.get("/sales/passengers/?lastname=dup")
    assert list(response.context["page_obj"]) == [match]


def test_detail_contains_only_passengers_tickets(client):
    employee = login_role(client)
    passenger = PassengerFactory()
    ticket = TicketFactory(
        client=passenger,
        buy__client=passenger,
        buy__emp=employee,
        ticketid="CB00000001",
    )
    other = TicketFactory(buy__emp=employee, ticketid="CB00000002")
    body = client.get(f"/sales/passengers/{passenger.clientid}/").content.decode()
    assert ticket.ticketid in body
    assert ticket.flight.flightnum in body
    assert other.ticketid not in body


def test_create_redirects_saves_and_reports_success(client):
    login_role(client)
    response = client.post("/sales/passengers/new/", passenger_data())
    passenger = PassengerFactory._meta.model.objects.get(email="jean.martin@example.com")
    assert response.status_code == 302
    assert response.url == f"/sales/passengers/{passenger.clientid}/"
    assert f"Passenger {passenger.clientid} saved." in [
        str(message) for message in get_messages(response.wsgi_request)
    ]


def test_edit_preserves_clientid(client):
    login_role(client)
    passenger = PassengerFactory(firstname="Old")
    response = client.post(
        f"/sales/passengers/{passenger.clientid}/edit/",
        passenger_data(firstname="New", email=passenger.email),
    )
    passenger.refresh_from_db()
    assert response.url == f"/sales/passengers/{passenger.clientid}/"
    assert passenger.firstname == "New"


def test_duplicate_email_warns_but_saves(client):
    login_role(client)
    PassengerFactory(email="duplicate@example.com")
    response = client.post("/sales/passengers/new/", passenger_data(email="DUPLICATE@example.com"))
    assert response.status_code == 302
    assert PassengerFactory._meta.model.objects.filter(email="DUPLICATE@example.com").exists()
    assert PASSENGER_EMAIL_WARNING in [
        str(message) for message in get_messages(response.wsgi_request)
    ]


def test_invalid_passenger_create_reports_errors_without_writing(role_client):
    client = role_client(Role.SALES)
    before = Passenger.objects.count()

    response = client.post(
        reverse("sales:passenger_create"),
        passenger_data(firstname="", email="not-an-email"),
    )

    content = response.content.decode()
    assert response.status_code == 200
    assert "This field is required." in content
    assert "Enter a valid email address." in content
    assert Passenger.objects.count() == before


@pytest.mark.parametrize("url", ["/sales/passengers/999999/", "/sales/passengers/999999/edit/"])
def test_missing_passenger_returns_404(client, url):
    login_role(client)
    assert client.get(url).status_code == 404
