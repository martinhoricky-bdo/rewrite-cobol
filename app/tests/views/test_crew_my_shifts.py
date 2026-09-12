from datetime import date, time

import pytest
from freezegun import freeze_time

from tests.factories import (
    CrewFactory,
    FlightFactory,
    ShiftFactory,
)

pytestmark = pytest.mark.django_db


@freeze_time("2026-09-12")
def test_crew_member_sees_own_upcoming_shift_and_flight(client, employee_of):
    employee = employee_of("crew")
    crew = CrewFactory(commander=employee)
    shift = ShiftFactory(
        crew=crew, shiftdate=date(2026, 9, 13), begintime=time(8), endtime=time(16)
    )
    FlightFactory(shift=shift, flightdate=shift.shiftdate, flightnum="CB2204")
    other_shift = ShiftFactory(shiftdate=date(2026, 9, 13))
    FlightFactory(shift=other_shift, flightdate=other_shift.shiftdate, flightnum="CB9999")
    client.force_login(employee.user)

    response = client.get("/crew/my-shifts/")

    assert response.status_code == 200
    assert b"CB2204" in response.content
    assert b"CB9999" not in response.content


@freeze_time("2026-09-12")
def test_past_shifts_only_appear_when_requested(client, employee_of):
    employee = employee_of("crew")
    shift = ShiftFactory(crew=CrewFactory(copilote=employee), shiftdate=date(2026, 9, 11))
    FlightFactory(shift=shift, flightdate=shift.shiftdate, flightnum="CB2205")
    client.force_login(employee.user)
    assert b"CB2205" not in client.get("/crew/my-shifts/").content
    assert b"CB2205" in client.get("/crew/my-shifts/?past=1").content
    assert client.get("/crew/my-shifts/?past=invalid").status_code == 200
