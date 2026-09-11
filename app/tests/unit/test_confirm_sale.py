import threading
from datetime import datetime
from decimal import Decimal

import pytest
from django.db import connection, connections

from core.messages import E_SEL_05_ID, E_SEL_10, E_SEL_11
from sales.models import Buy, Ticket
from sales.services import SaleError, SaleQuote, confirm_sale
from tests.factories import EmployeeFactory, FlightFactory, PassengerFactory, TicketFactory

pytestmark = pytest.mark.django_db


def make_quote(flight, client_id, count):
    return SaleQuote(
        flight_id=flight.pk,
        flightnum=flight.flightnum,
        flightdate=flight.flightdate,
        deptime=flight.deptime,
        arrtime=flight.arrtime,
        airportdep=flight.airportdep_id,
        airportarr=flight.airportarr_id,
        client_id=client_id,
        client_name="First Passenger",
        count=count,
        unit_price=Decimal("120.99"),
        total_price=Decimal("120.99") * count,
        free_seats=flight.airplane.numseats,
    )


def test_confirm_sale_creates_buy_and_consecutive_tickets():
    with connection.cursor() as cursor:
        cursor.execute("ALTER SEQUENCE ticket_ticketid_seq RESTART WITH 1")
    flight = FlightFactory()
    passengers = PassengerFactory.create_batch(3)
    seller = EmployeeFactory()
    buy = confirm_sale(
        quote=make_quote(flight, passengers[0].pk, 3),
        client_ids=[passenger.pk for passenger in passengers],
        seller=seller,
        now=datetime(2026, 9, 11, 12, 34, 56, 999),
    )
    assert Buy.objects.count() == 1
    assert buy.price == Decimal("362.97")
    assert buy.emp == seller
    assert buy.client == passengers[0]
    tickets = list(Ticket.objects.order_by("ticketid"))
    assert [ticket.ticketid for ticket in tickets] == ["CB00000001", "CB00000002", "CB00000003"]
    assert [ticket.seat for ticket in tickets] == ["A01", "B01", "C01"]


@pytest.mark.parametrize(
    ("kind", "code"),
    [("duplicate", "E_SEL_11"), ("missing", "E_SEL_05"), ("existing", "E_SEL_10")],
)
def test_confirm_sale_rejects_invalid_passengers_and_rolls_back(kind, code):
    flight = FlightFactory()
    passenger = PassengerFactory()
    other = PassengerFactory()
    seller = EmployeeFactory()
    ids = [passenger.pk, other.pk]
    expected = ""
    if kind == "duplicate":
        ids = [passenger.pk, passenger.pk]
        expected = E_SEL_11.format(id=passenger.pk)
    elif kind == "missing":
        ids[1] = 999999
        expected = E_SEL_05_ID.format(id=999999)
    else:
        TicketFactory(flight=flight, client=passenger)
        expected = E_SEL_10.format(id=passenger.pk)
    initial_buys = Buy.objects.count()
    with pytest.raises(SaleError) as error:
        confirm_sale(
            quote=make_quote(flight, passenger.pk, 2),
            client_ids=ids,
            seller=seller,
            now=datetime(2026, 9, 11, 12),
        )
    assert error.value.code == code
    assert error.value.message == expected
    assert Buy.objects.count() == initial_buys


@pytest.mark.django_db(transaction=True)
def test_concurrent_sales_cannot_exceed_capacity():
    flight = FlightFactory(airplane__numseats=1)
    passengers = PassengerFactory.create_batch(2)
    seller = EmployeeFactory()
    barrier = threading.Barrier(2)
    outcomes = []

    def sell(passenger):
        connections.close_all()
        barrier.wait()
        try:
            confirm_sale(
                quote=make_quote(flight, passenger.pk, 1),
                client_ids=[passenger.pk],
                seller=seller,
                now=datetime(2026, 9, 11, 12),
            )
        except SaleError as error:
            outcomes.append(error.code)
        else:
            outcomes.append("success")
        finally:
            connections.close_all()

    threads = [threading.Thread(target=sell, args=(passenger,)) for passenger in passengers]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(outcomes) == ["E_SEL_08", "success"]
    assert Buy.objects.count() == 1
    assert Ticket.objects.count() == 1
