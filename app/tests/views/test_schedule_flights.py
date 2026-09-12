from datetime import date

import pytest
from django.urls import reverse

from core.messages import E_REF_01
from operations.models import Flight
from tests.factories import (
    DepartmentFactory,
    EmployeeFactory,
    FlightFactory,
    TicketFactory,
    UserFactory,
)

pytestmark = pytest.mark.django_db


def login_as(client, deptid=9):
    user = UserFactory()
    EmployeeFactory(user=user, dept=DepartmentFactory(deptid=deptid))
    client.force_login(user)


def flight_data(flight, **updates):
    data = {
        "flightnum": "CB8765",
        "flightdate": "2026-04-01",
        "deptime": "10:00",
        "arrtime": "12:00",
        "airplane": flight.airplane_id,
        "airportdep": flight.airportdep_id,
        "airportarr": flight.airportarr_id,
        "shift": flight.shift_id,
        "price": "99.00",
    }
    data.update(updates)
    return data


def test_list_filters_create_and_edit(client):
    login_as(client)
    flight = FlightFactory(flightdate=date(2026, 4, 1), flightnum="CB1000")
    response = client.get(
        reverse("schedule:flights"),
        {"date_from": "2026-04-01", "date_to": "2026-04-01", "airport": flight.airportdep_id},
    )
    assert response.status_code == 200
    assert "CB1000" in response.content.decode()
    response = client.post(reverse("schedule:flight_create"), flight_data(flight))
    assert response.status_code == 302
    created = Flight.objects.get(flightnum="CB8765")
    assert created.totpass == created.airplane.numseats
    response = client.post(
        reverse("schedule:flight_edit", args=[created.pk]),
        flight_data(created, price="88.00"),
    )
    assert response.status_code == 302
    created.refresh_from_db()
    assert str(created.price) == "88.00"


def test_delete_and_generate(client):
    login_as(client)
    unused = FlightFactory()
    client.post(reverse("schedule:flight_delete", args=[unused.pk]))
    assert not Flight.objects.filter(pk=unused.pk).exists()
    used = FlightFactory()
    TicketFactory(flight=used)
    response = client.post(reverse("schedule:flight_delete", args=[used.pk]), follow=True)
    assert E_REF_01.format(Entity="Flight", n=1, related="tickets") in response.content.decode()

    template = FlightFactory(flightdate=date(2026, 1, 1), flightnum="CB7654")
    response = client.post(
        reverse("schedule:flights_generate"),
        {
            "template": template.pk,
            "date_from": "2026-05-01",
            "date_to": "2026-05-07",
            "weekdays": [str(day) for day in range(7)],
        },
        follow=True,
    )
    assert "Generated 7 flights, skipped 0 existing." in response.content.decode()


@pytest.mark.parametrize(
    ("name", "args", "method"),
    [
        ("schedule:flights", [], "get"),
        ("schedule:flight_create", [], "get"),
        ("schedule:flight_create", [], "post"),
        ("schedule:flights_generate", [], "get"),
        ("schedule:flights_generate", [], "post"),
        ("schedule:flight_edit", [1], "get"),
        ("schedule:flight_edit", [1], "post"),
        ("schedule:flight_delete", [1], "get"),
        ("schedule:flight_delete", [1], "post"),
    ],
)
def test_sales_role_gets_403_for_every_schedule_action(client, name, args, method):
    login_as(client, 7)
    assert getattr(client, method)(reverse(name, args=args)).status_code == 403
