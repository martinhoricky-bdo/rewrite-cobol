from datetime import date

import pytest

from tests.factories import (
    CrewFactory,
    DepartmentFactory,
    EmployeeFactory,
    FlightFactory,
    ShiftFactory,
    TicketFactory,
)

pytestmark = pytest.mark.django_db


def test_flight_queryset_helpers():
    matching = FlightFactory(flightdate=date(2026, 1, 10))
    FlightFactory(flightdate=date(2026, 2, 10))
    TicketFactory(flight=matching)

    flight = type(matching).objects.in_period(date(2026, 1, 1), date(2026, 1, 31)).with_sold().get()
    assert flight == matching
    assert flight.sold == 1
    related = type(matching).objects.with_related().get(pk=matching.pk)
    assert related.airportdep.name
    assert related.airportarr.name
    assert related.airplane.type
    assert related.shift.shiftid


@pytest.mark.parametrize(
    "member_field",
    ["commander", "copilote", "fachief", "fliattendant1", "fliattendant2", "fliattendant3"],
)
def test_crew_with_member_checks_every_position(member_field):
    employee = EmployeeFactory()
    crew = CrewFactory(**{member_field: employee})

    assert list(type(crew).objects.with_member(employee)) == [crew]


def test_crew_annotation_and_related_helpers():
    crew = CrewFactory()
    ShiftFactory(crew=crew)

    annotated = type(crew).objects.with_shift_count().get(pk=crew.pk)
    assert annotated.shift_count == 1
    related = type(crew).objects.with_members().get(pk=crew.pk)
    assert len(related.members()) == 6


def test_shift_queryset_helpers():
    matching = ShiftFactory(shiftdate=date(2026, 1, 10))
    ShiftFactory(shiftdate=date(2026, 2, 10))
    FlightFactory(shift=matching)

    shift = type(matching).objects.in_period(date(2026, 1, 1), date(2026, 1, 31)).get()
    assert shift == matching
    assert list(type(matching).objects.for_crew(matching.crew_id)) == [matching]
    assert type(matching).objects.with_flight_count().get(pk=matching.pk).flight_count == 1


def test_employee_queryset_helpers():
    sales = DepartmentFactory(name="Sales")
    employee = EmployeeFactory(firstname="Alice", lastname="Jones", dept=sales)
    EmployeeFactory(firstname="Bob")

    model = type(employee)
    assert list(model.objects.search("sales")) == [employee]
    assert list(model.objects.name_starts_with("ali")) == [employee]
    assert list(model.objects.in_department(sales.pk)) == [employee]
