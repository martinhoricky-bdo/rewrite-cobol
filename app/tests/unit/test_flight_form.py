from datetime import date
from decimal import Decimal

import pytest

from operations.forms import FlightForm
from tests.factories import FlightFactory

pytestmark = pytest.mark.django_db


def data_for(flight, **updates):
    data = {
        "flightnum": "cb9876",
        "flightdate": date(2026, 4, 1),
        "deptime": "10:00",
        "arrtime": "12:00",
        "airplane": flight.airplane_id,
        "airportdep": flight.airportdep_id,
        "airportarr": flight.airportarr_id,
        "shift": flight.shift_id,
        "price": Decimal("10.00"),
    }
    data.update(updates)
    return data


def test_flight_number_is_uppercase_and_validated():
    related = FlightFactory()
    form = FlightForm(data=data_for(related))
    assert form.is_valid(), form.errors
    assert form.save().flightnum == "CB9876"
    form = FlightForm(data=data_for(related, flightnum="XX1234"))
    assert not form.is_valid()


@pytest.mark.parametrize("updates", [{"price": "0"}, {"price": "-1"}])
def test_price_must_be_positive(updates):
    assert not FlightForm(data=data_for(FlightFactory(), **updates)).is_valid()


def test_airports_must_differ_and_flight_must_be_unique():
    related = FlightFactory(flightnum="CB9876", flightdate=date(2026, 4, 1))
    assert not FlightForm(data=data_for(related, airportarr=related.airportdep_id)).is_valid()
    form = FlightForm(data=data_for(related))
    assert not form.is_valid()
    assert "already exists" in form.non_field_errors()[0]
