from datetime import date, time

import pytest
from django.urls import reverse

from tests.factories import (
    BuyFactory,
    DepartmentFactory,
    EmployeeFactory,
    FlightFactory,
    PassengerFactory,
    TicketFactory,
)

pytestmark = pytest.mark.django_db


def login_role(client, deptid):
    employee = EmployeeFactory(dept=DepartmentFactory(deptid=deptid), with_user=True)
    client.force_login(employee.user)


def sale_with_tickets():
    buy = BuyFactory()
    flight = FlightFactory(flightdate=date(2026, 10, 1), deptime=time(10))
    passengers = [
        PassengerFactory(firstname="Alice", lastname="Martin"),
        PassengerFactory(firstname="Bruno", lastname="Petit"),
        PassengerFactory(firstname="Claire", lastname="Robert"),
    ]
    for number, (passenger, seat) in enumerate(
        zip(passengers, ("A01", "B01", "C01"), strict=True), start=1
    ):
        TicketFactory(
            ticketid=f"CB{number:08d}",
            buy=buy,
            client=passenger,
            flight=flight,
            seat=seat,
        )
    return buy


def test_all_boarding_passes_are_rendered(client):
    login_role(client, 7)
    buy = sale_with_tickets()

    response = client.get(reverse("sales:boarding_passes", args=[buy.buyid]))

    assert response.status_code == 200
    body = response.content.decode()
    assert body.count("BOARDING PASS") == 3
    for name, seat in (
        ("ALICE MARTIN", "A01"),
        ("BRUNO PETIT", "B01"),
        ("CLAIRE ROBERT", "C01"),
    ):
        assert name in body
        assert seat in body


def test_single_boarding_pass_still_uses_shared_content(client):
    login_role(client, 7)
    buy = sale_with_tickets()
    ticket = buy.tickets.order_by("ticketid").first()

    response = client.get(reverse("sales:boarding_pass", args=[ticket.ticketid]))

    assert response.status_code == 200
    assert response.content.decode().count("BOARDING PASS") == 1
    assert "ALICE MARTIN" in response.content.decode()


def test_missing_buy_returns_404(client):
    login_role(client, 7)
    assert client.get(reverse("sales:boarding_passes", args=[999999])).status_code == 404


def test_buy_detail_links_to_both_print_views(client):
    login_role(client, 7)
    buy = BuyFactory()
    response = client.get(reverse("sales:buy_detail", args=[buy.buyid]))
    body = response.content.decode()
    assert reverse("sales:receipt", args=[buy.buyid]) in body
    assert reverse("sales:boarding_passes", args=[buy.buyid]) in body
