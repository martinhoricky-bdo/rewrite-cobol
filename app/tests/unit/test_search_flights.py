from datetime import date, time, timedelta

import pytest

from operations.services import search_flights
from tests.factories import AirplaneFactory, AirportFactory, FlightFactory, TicketFactory

pytestmark = pytest.mark.django_db

TODAY = date(2026, 9, 11)


def search(**overrides):
    parameters = {
        "flightnum": None,
        "flightdate": None,
        "airportdep": None,
        "airportarr": None,
        "today": TODAY,
    }
    parameters.update(overrides)
    return search_flights(**parameters)


def test_number_without_date_is_case_insensitive_and_excludes_past_flights():
    past = FlightFactory(flightnum="CB1104", flightdate=TODAY - timedelta(days=1))
    future = FlightFactory(flightnum="CB1104", flightdate=TODAY + timedelta(days=1))
    assert list(search(flightnum=" cb1104 ")) == [future]
    assert past not in search(flightnum="CB1104")


def test_date_alone_filters_exactly():
    match = FlightFactory(flightdate=TODAY)
    FlightFactory(flightdate=TODAY + timedelta(days=1))
    assert list(search(flightdate=TODAY)) == [match]


def test_number_and_date_are_combined():
    match = FlightFactory(flightnum="CB1104", flightdate=TODAY)
    FlightFactory(flightnum="CB1105", flightdate=TODAY)
    assert list(search(flightnum="CB1104", flightdate=TODAY)) == [match]


def test_departure_without_date_is_case_insensitive_and_excludes_past():
    cdg = AirportFactory(airportid="CDG")
    FlightFactory(airportdep=cdg, flightdate=TODAY - timedelta(days=1))
    match = FlightFactory(airportdep=cdg, flightdate=TODAY)
    assert list(search(airportdep=" cdg ")) == [match]


def test_departure_arrival_and_date_are_combined():
    cdg = AirportFactory(airportid="CDG")
    lhr = AirportFactory(airportid="LHR")
    match = FlightFactory(airportdep=cdg, airportarr=lhr, flightdate=TODAY)
    FlightFactory(airportdep=cdg, flightdate=TODAY)
    assert list(search(airportdep="CDG", airportarr="lhr", flightdate=TODAY)) == [match]


def test_conflicting_number_and_airport_returns_nothing():
    flight = FlightFactory(flightnum="CB1104", flightdate=TODAY)
    assert not search(flightnum="CB1104", airportdep="ZZZ", flightdate=flight.flightdate).exists()


def test_results_are_ordered_by_date_time_and_number():
    later_date = FlightFactory(flightdate=TODAY + timedelta(days=1), deptime=time(8))
    later_number = FlightFactory(flightdate=TODAY, deptime=time(9), flightnum="CB9000")
    earlier_number = FlightFactory(flightdate=TODAY, deptime=time(9), flightnum="CB1000")
    assert list(search(airportdep=earlier_number.airportdep_id)) == [earlier_number]
    # Use an unfiltered service call here to exercise ordering independently.
    assert list(search()) == [earlier_number, later_number, later_date]


def test_free_seats_uses_airplane_capacity_minus_ticket_count():
    flight = FlightFactory(airplane=AirplaneFactory(numseats=230), flightdate=TODAY)
    TicketFactory(flight=flight, seat="A01")
    TicketFactory(flight=flight, seat="A02")
    result = search(flightnum=flight.flightnum).get()
    assert result.sold == 2
    assert result.free_seats == 228
