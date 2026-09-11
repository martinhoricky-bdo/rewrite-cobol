from datetime import date, time, timedelta

import pytest

from sales.services import search_tickets
from tests.factories import FlightFactory, PassengerFactory, TicketFactory

pytestmark = pytest.mark.django_db


def make_ticket(**kwargs):
    passenger = kwargs.pop("client", PassengerFactory(firstname="MAXIME", lastname="DUPRAT"))
    return TicketFactory(client=passenger, buy__client=passenger, **kwargs)


def test_ticket_id_takes_priority_over_every_other_filter():
    wanted = make_ticket(ticketid="CB00000001")
    make_ticket(ticketid="CB00000002")
    assert list(search_tickets(ticketid="cb00000001", clientid=999)) == [wanted]


@pytest.mark.parametrize(
    ("filters", "match"),
    [
        ({"flightnum": "cb2204"}, True),
        ({"flightdate": date(2026, 9, 11)}, True),
        ({"flightnum": "CB2204", "flightdate": date(2026, 9, 11)}, True),
        ({"flightnum": "CB9999", "flightdate": date(2026, 9, 11)}, False),
    ],
)
def test_client_search_accepts_optional_flight_filters(filters, match):
    ticket = make_ticket(flight=FlightFactory(flightnum="CB2204", flightdate=date(2026, 9, 11)))
    results = list(search_tickets(clientid=ticket.client_id, **filters))
    assert (ticket in results) is match


def test_name_search_is_case_insensitive_and_can_filter_flight_number():
    ticket = make_ticket(flight=FlightFactory(flightnum="CB2204"))
    assert list(search_tickets(firstname="maxime", lastname="DUPRAT")) == [ticket]
    assert list(search_tickets(firstname="maxime", lastname="duprat", flightnum="cb2204")) == [
        ticket
    ]


def test_results_are_ordered_by_date_time_and_ticket_id():
    base = date(2026, 9, 11)
    late = make_ticket(
        ticketid="CB00000003", flight=FlightFactory(flightdate=base, deptime=time(12))
    )
    next_day = make_ticket(
        ticketid="CB00000001", flight=FlightFactory(flightdate=base + timedelta(days=1))
    )
    early = make_ticket(
        ticketid="CB00000002", flight=FlightFactory(flightdate=base, deptime=time(8))
    )
    assert list(search_tickets(firstname="maxime", lastname="duprat")) == [early, late, next_day]


def test_related_rows_are_eager_loaded(django_assert_num_queries):
    passenger = PassengerFactory(firstname="MAXIME", lastname="DUPRAT")
    for _ in range(10):
        make_ticket(client=passenger)
    with django_assert_num_queries(1):
        for ticket in search_tickets(firstname="maxime", lastname="duprat"):
            str(ticket.client)
            str(ticket.flight.airportdep)
            str(ticket.flight.airportarr)
            str(ticket.buy)
