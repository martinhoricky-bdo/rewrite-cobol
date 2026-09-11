from datetime import time

import pytest
from django.db import IntegrityError, transaction

from operations.models import Flight
from sales.models import Ticket
from tests.factories import (
    AirplaneFactory,
    AirportFactory,
    FlightFactory,
    PassengerFactory,
    ShiftFactory,
    TicketFactory,
)

pytestmark = pytest.mark.django_db


def assert_integrity_error(model, **changes):
    original = model.objects.first()
    values = {
        field.name: getattr(original, field.name)
        for field in model._meta.fields
        if not field.primary_key
    }
    values.update(changes)
    with pytest.raises(IntegrityError), transaction.atomic():
        model.objects.create(**values)


def test_flight_number_and_date_are_unique():
    flight = FlightFactory()
    assert_integrity_error(Flight, flightnum=flight.flightnum, flightdate=flight.flightdate)


def test_ticket_seat_is_unique_per_flight():
    ticket = TicketFactory()
    assert_integrity_error(
        Ticket,
        ticketid="CB99999998",
        flight=ticket.flight,
        seat=ticket.seat,
        client=PassengerFactory(),
    )


def test_ticket_client_is_unique_per_flight():
    ticket = TicketFactory()
    assert_integrity_error(
        Ticket,
        ticketid="CB99999997",
        flight=ticket.flight,
        client=ticket.client,
        seat="F99",
    )


def test_flight_airports_must_differ():
    airport = AirportFactory()
    with pytest.raises(IntegrityError), transaction.atomic():
        FlightFactory(airportdep=airport, airportarr=airport)


@pytest.mark.parametrize("begin,end", [(time(10), time(10)), (time(11), time(10))])
def test_shift_must_end_after_it_begins(begin, end):
    with pytest.raises(IntegrityError), transaction.atomic():
        ShiftFactory(begintime=begin, endtime=end)


def test_airplane_must_have_seats():
    with pytest.raises(IntegrityError), transaction.atomic():
        AirplaneFactory(numseats=0)
