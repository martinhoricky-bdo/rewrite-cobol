import pytest
from django.urls import reverse

from core.messages import E_REF_01
from fleet.models import Airplane
from tests.factories import (
    DepartmentFactory,
    EmployeeFactory,
    FlightFactory,
    TicketFactory,
    UserFactory,
)

pytestmark = pytest.mark.django_db


def login_as(client, deptid=6):
    user = UserFactory()
    EmployeeFactory(user=user, dept=DepartmentFactory(deptid=deptid))
    client.force_login(user)


def airplane_data(identifier="ab", seats=100):
    return {"airplaneid": identifier, "type": "A320", "numseats": seats, "totalfuel": 1000}


def test_airplane_crud_uppercase_and_limits(client):
    login_as(client)
    assert client.post(reverse("it:airplane_create"), airplane_data()).status_code == 302
    assert Airplane.objects.filter(pk="AB").exists()
    assert client.post(reverse("it:airplane_create"), airplane_data()).status_code == 200
    response = client.post(reverse("it:airplane_create"), airplane_data("TOOLONGID"))
    assert "at most 8 characters" in response.content.decode()
    response = client.post(reverse("it:airplane_create"), airplane_data("OK", 1000))
    assert "between 1 and 999" in response.content.decode()


def test_airplane_cannot_shrink_below_sold_tickets(client):
    login_as(client)
    flight = FlightFactory()
    TicketFactory(flight=flight)
    TicketFactory(flight=flight)
    response = client.post(
        reverse("it:airplane_edit", args=[flight.airplane_id]), airplane_data(flight.airplane_id, 1)
    )
    assert f"2 tickets are already sold on flight {flight.flightnum}." in response.content.decode()


def test_airplane_delete_reference_and_permissions(client):
    login_as(client, 9)
    flight = FlightFactory()
    response = client.post(reverse("it:airplane_delete", args=[flight.airplane_id]), follow=True)
    assert E_REF_01.format(Entity="Airplane", n=1, related="flights") in response.content.decode()
    assert Airplane.objects.filter(pk=flight.airplane_id).exists()
    client.logout()
    login_as(client, 7)
    assert client.get(reverse("it:airplanes")).status_code == 403


def test_airplane_without_flights_can_be_deleted(client):
    login_as(client)
    airplane = Airplane.objects.create(airplaneid="FREE", type="A320", numseats=100, totalfuel=1000)

    response = client.post(reverse("it:airplane_delete", args=[airplane.pk]), follow=True)

    assert response.status_code == 200
    assert not Airplane.objects.filter(pk=airplane.pk).exists()
    assert f"Airplane {airplane.pk} deleted." in response.content.decode()


@pytest.mark.parametrize("deptid", [6, 9])
def test_it_and_schedule_can_view_airplanes(client, deptid):
    login_as(client, deptid)
    assert client.get(reverse("it:airplanes")).status_code == 200
