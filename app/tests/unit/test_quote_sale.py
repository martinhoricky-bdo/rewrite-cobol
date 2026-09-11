from datetime import date, time, timedelta
from decimal import Decimal

import pytest

from core.messages import E_SEL_05, E_SEL_06, E_SEL_07, E_SEL_08
from sales.services import SaleError, SaleQuote, quote_sale
from tests.factories import AirplaneFactory, FlightFactory, PassengerFactory

pytestmark = pytest.mark.django_db
TODAY = date(2026, 9, 11)


def assert_sale_error(code, message, **kwargs):
    with pytest.raises(SaleError) as caught:
        quote_sale(today=TODAY, **kwargs)
    assert caught.value.code == code
    assert caught.value.message == message


def test_missing_client_is_checked_first():
    assert_sale_error(
        "E_SEL_05",
        E_SEL_05,
        clientid=999999,
        flightnum="CB9999",
        flightdate=TODAY,
        count=1,
    )


def test_missing_flight():
    passenger = PassengerFactory()
    assert_sale_error(
        "E_SEL_06",
        E_SEL_06,
        clientid=passenger.pk,
        flightnum="CB9999",
        flightdate=TODAY,
        count=1,
    )


def test_departed_flight():
    passenger = PassengerFactory()
    flight = FlightFactory(flightdate=TODAY - timedelta(days=1))
    assert_sale_error(
        "E_SEL_07",
        E_SEL_07,
        clientid=passenger.pk,
        flightnum=flight.flightnum,
        flightdate=flight.flightdate,
        count=1,
    )


def test_insufficient_capacity_reports_remaining_seats():
    passenger = PassengerFactory()
    flight = FlightFactory(airplane=AirplaneFactory(numseats=2), flightdate=TODAY)
    assert_sale_error(
        "E_SEL_08",
        E_SEL_08.format(n=2),
        clientid=passenger.pk,
        flightnum=flight.flightnum,
        flightdate=flight.flightdate,
        count=3,
    )


def test_quote_calculates_decimal_total_and_flight_number_is_case_insensitive():
    passenger = PassengerFactory(firstname="Ada", lastname="Lovelace")
    flight = FlightFactory(flightnum="CB1104", flightdate=TODAY, price=Decimal("120.99"))
    quote = quote_sale(
        clientid=passenger.pk,
        flightnum="cb1104",
        flightdate=flight.flightdate,
        count=3,
        today=TODAY,
    )
    assert quote.total_price == Decimal("362.97")
    assert isinstance(quote.total_price, Decimal)
    assert quote.client_name == "Ada Lovelace"


def test_quote_session_round_trip():
    quote = SaleQuote(
        flight_id=4,
        flightnum="CB1104",
        flightdate=TODAY,
        deptime=time(10, 5),
        arrtime=time(12, 30),
        airportdep="CDG",
        airportarr="LHR",
        client_id=641,
        client_name="Ada Lovelace",
        count=3,
        unit_price=Decimal("120.99"),
        total_price=Decimal("362.97"),
        free_seats=10,
    )
    data = quote.to_session()
    assert data["flightdate"] == "2026-09-11"
    assert data["deptime"] == "10:05"
    assert data["unit_price"] == "120.99"
    assert SaleQuote.from_session(data) == quote
