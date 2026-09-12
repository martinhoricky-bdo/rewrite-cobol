from datetime import date, timedelta

import pytest

from operations.forms import FlightGenerateForm
from operations.models import Flight, Shift
from operations.services import generate_flights
from tests.factories import FlightFactory, ShiftFactory

pytestmark = pytest.mark.django_db


def test_generate_all_days_and_skip_existing():
    template = FlightFactory(flightdate=date(2026, 1, 1), flightnum="CB1234")
    start = date(2026, 2, 1)
    result = generate_flights(template, start, start + timedelta(days=6), set(range(7)))
    assert result.created == 7
    assert result.skipped == 0
    assert Flight.objects.filter(flightnum="CB1234", flightdate__gte=start).count() == 7

    Flight.objects.filter(flightnum="CB1234", flightdate=start).delete()
    result = generate_flights(template, start, start + timedelta(days=6), set(range(7)))
    assert result.created == 1
    assert result.skipped == 6


def test_generate_selected_weekdays_and_reuses_or_creates_shift():
    template = FlightFactory(flightdate=date(2026, 1, 1), flightnum="CB2345")
    start = date(2026, 2, 2)  # Monday
    existing = ShiftFactory(shiftdate=start, crew=template.shift.crew)
    result = generate_flights(template, start, start + timedelta(days=4), {0, 4})
    assert result.created == 2
    assert Flight.objects.get(flightnum="CB2345", flightdate=start).shift == existing
    assert Shift.objects.filter(
        shiftdate=start + timedelta(days=4), crew=template.shift.crew
    ).exists()


def test_generation_form_rejects_period_over_92_days():
    template = FlightFactory()
    form = FlightGenerateForm(
        data={
            "template": template.pk,
            "date_from": "2026-01-01",
            "date_to": "2026-04-03",
            "weekdays": ["0"],
        }
    )
    assert not form.is_valid()
    assert "must not exceed 92 days" in form.errors["date_to"][0]
