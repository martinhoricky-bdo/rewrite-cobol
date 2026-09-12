from datetime import date
from decimal import Decimal

import pytest

from reports.services import dashboard_report
from tests.factories import (
    BuyFactory,
    EmployeeFactory,
    FlightFactory,
    PassengerFactory,
    TicketFactory,
)

pytestmark = pytest.mark.django_db


def _tickets(flight, buy, count, prefix, *, seat_offset=0):
    for number in range(count):
        seat_number = number + seat_offset
        TicketFactory(
            ticketid=f"CB{prefix:02d}{number:06d}",
            flight=flight,
            buy=buy,
            client=PassengerFactory(),
            seat=f"{chr(65 + seat_number % 6)}{seat_number // 6 + 1:02d}",
        )


def test_dashboard_report_aggregates_sales_routes_and_load_factor():
    seller_one = EmployeeFactory()
    seller_two = EmployeeFactory()
    flight = FlightFactory(
        flightdate=date(2026, 9, 10),
        airplane__numseats=100,
        airportdep__airportid="CDG",
        airportarr__airportid="LHR",
    )
    other_route = FlightFactory(
        flightdate=date(2026, 9, 11),
        airplane__numseats=100,
        airportdep__airportid="FCO",
        airportarr__airportid="MAD",
    )
    buy_one = BuyFactory(buydate=date(2026, 9, 10), price=Decimal("200.00"), emp=seller_one)
    buy_two = BuyFactory(buydate=date(2026, 9, 11), price=Decimal("50.00"), emp=seller_two)
    outside = BuyFactory(buydate=date(2026, 8, 31), price=Decimal("999.00"), emp=seller_one)
    _tickets(flight, buy_one, 25, 11)
    _tickets(other_route, buy_two, 2, 12)
    _tickets(other_route, outside, 1, 13, seat_offset=2)

    report = dashboard_report(date(2026, 9, 1), date(2026, 9, 30))

    assert report["sales"] == 2
    assert report["revenue"] == Decimal("250.00")
    assert report["tickets"] == 27
    assert report["flights"] == 2
    assert report["average_load_factor"] == Decimal("14.00")
    routes = list(report["top_routes"])
    assert routes[0]["airportdep_id"] == "CDG"
    assert routes[0]["ticket_count"] == 25
    sellers = list(report["sales_by_seller"])
    assert {row["emp_id"]: row["sale_count"] for row in sellers} == {
        seller_one.pk: 1,
        seller_two.pk: 1,
    }
    loads = list(report["load_by_flight_number"])
    assert loads[0]["load_factor"] == Decimal("25.00")


def test_dashboard_report_excludes_buys_outside_period():
    BuyFactory(buydate=date(2026, 8, 31), price=Decimal("99.00"))
    report = dashboard_report(date(2026, 9, 1), date(2026, 9, 30))
    assert report["sales"] == 0
    assert report["revenue"] == Decimal("0.00")
