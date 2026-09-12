from datetime import date

import pytest

from hr.forms import EmployeeFilterForm
from operations.forms import FlightFilterForm, ShiftFilterForm
from tests.factories import CrewFactory, DepartmentFactory

pytestmark = pytest.mark.django_db


def test_flight_filter_defaults_and_invalid_date():
    default_start, default_end = date(2026, 1, 1), date(2026, 1, 31)

    empty = FlightFilterForm({})
    invalid = FlightFilterForm({"date_from": "bad", "date_to": "also-bad"})

    assert empty.value("date_from", default_start) == default_start
    assert empty.value("date_to", default_end) == default_end
    assert invalid.value("date_from", default_start) == default_start
    assert invalid.value("date_to", default_end) == default_end


def test_shift_filter_accepts_crew_and_ignores_invalid_value():
    crew = CrewFactory()

    assert ShiftFilterForm({"crew": crew.pk}).value("crew") == crew
    assert ShiftFilterForm({"crew": "bad"}).value("crew") is None
    assert ShiftFilterForm().fields["crew"].empty_label == "All"


def test_employee_filter_accepts_department_and_ignores_invalid_value():
    department = DepartmentFactory()

    assert EmployeeFilterForm({"dept": department.pk}).value("dept") == department
    assert EmployeeFilterForm({"dept": "bad"}).value("dept") is None
    assert EmployeeFilterForm().fields["dept"].empty_label == "All"
