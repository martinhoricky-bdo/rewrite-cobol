from datetime import date

import pytest

from accounts.models import Department
from legacy_import.data import CREWS
from legacy_import.services import generate_flights, seed_reference_data
from operations.models import Crew, Flight, Shift
from tests.factories import EmployeeFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def crews():
    seed_reference_data()
    department = Department.objects.get(pk=1)
    result = {}
    for index, member_ids in enumerate(CREWS):
        members = [EmployeeFactory(empid=empid, dept=department) for empid in member_ids]
        result[index] = Crew.objects.create(
            commander=members[0],
            copilote=members[1],
            fachief=members[2],
            fliattendant1=members[3],
            fliattendant2=members[4],
            fliattendant3=members[5],
        )
    return result


def test_generate_flights_for_three_days_and_skip_existing(crews):
    start = date(2030, 1, 1)

    generate_flights(start, 3, crews)

    assert Shift.objects.count() == 12
    assert Flight.objects.count() == 24
    existing = Flight.objects.get(flightnum="CB2204", flightdate=start)
    existing.price = "99.99"
    existing.save(update_fields=["price"])

    generate_flights(start, 3, crews)

    assert Shift.objects.count() == 12
    assert Flight.objects.count() == 24
    existing.refresh_from_db()
    assert str(existing.price) == "99.99"
