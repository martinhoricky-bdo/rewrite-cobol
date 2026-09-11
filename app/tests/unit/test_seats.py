import pytest

from core.messages import E_SEL_08
from sales.services import SaleError, assign_seats, seat_layout
from tests.factories import FlightFactory, TicketFactory

pytestmark = pytest.mark.django_db


def test_seat_layout_includes_partial_last_row():
    assert seat_layout(8) == ["A01", "B01", "C01", "D01", "E01", "F01", "A02", "B02"]


def test_assign_seats_skips_occupied_seats():
    flight = FlightFactory(airplane__numseats=8)
    TicketFactory(flight=flight, seat="A01")
    TicketFactory(flight=flight, seat="C01")
    assert assign_seats(flight, 2) == ["B01", "D01"]


def test_assign_seats_uses_partial_last_row():
    flight = FlightFactory(airplane__numseats=8)
    for seat in seat_layout(6):
        TicketFactory(flight=flight, seat=seat)
    assert assign_seats(flight, 2) == ["A02", "B02"]


def test_assign_seats_reports_remaining_capacity():
    flight = FlightFactory(airplane__numseats=1)
    TicketFactory(flight=flight, seat="A01")
    with pytest.raises(SaleError) as error:
        assign_seats(flight, 1)
    assert error.value.code == "E_SEL_08"
    assert error.value.message == E_SEL_08.format(n=0)
