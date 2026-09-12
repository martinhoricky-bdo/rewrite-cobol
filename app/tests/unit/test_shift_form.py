from datetime import date, time

import pytest

from operations.forms import ShiftForm
from tests.factories import CrewFactory, ShiftFactory

pytestmark = pytest.mark.django_db


def shift_data(crew, begin="09:00", end="17:00"):
    return {"shiftdate": "2026-10-01", "begintime": begin, "endtime": end, "crew": crew.pk}


@pytest.mark.parametrize(("begin", "end"), [("17:00", "09:00"), ("09:00", "09:00")])
def test_begin_must_be_before_end(begin, end):
    crew = CrewFactory()
    form = ShiftForm(data=shift_data(crew, begin, end))
    assert not form.is_valid()
    assert "Begin time must be before end time." in form.non_field_errors()


def test_overlapping_shift_is_rejected():
    crew = CrewFactory()
    ShiftFactory(crew=crew, shiftdate=date(2026, 10, 1), begintime=time(8), endtime=time(12))
    form = ShiftForm(data=shift_data(crew, "11:00", "15:00"))
    assert not form.is_valid()
    assert (
        f"Crew {crew.pk} already has a shift on 2026-10-01 overlapping this time."
        in form.non_field_errors()
    )


def test_non_overlapping_shift_is_valid():
    crew = CrewFactory()
    ShiftFactory(crew=crew, shiftdate=date(2026, 10, 1), begintime=time(8), endtime=time(12))
    assert ShiftForm(data=shift_data(crew, "12:00", "15:00")).is_valid()
