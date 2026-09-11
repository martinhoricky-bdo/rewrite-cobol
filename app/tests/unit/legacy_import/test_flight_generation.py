from datetime import date
from decimal import Decimal

import pytest

from accounts.models import Department, Employee
from legacy_import.data import CREWS
from legacy_import.services import generate_flights, seed_crews, seed_reference_data
from operations.models import Flight, Shift

pytestmark = pytest.mark.django_db


def test_generate_flights_creates_three_days_and_skips_existing():
    seed_reference_data()
    department = Department.objects.get(pk=4)
    for empid in {empid for crew in CREWS for empid in crew}:
        Employee.objects.create(
            empid=empid,
            firstname="Test",
            lastname=empid,
            addre="Test address",
            city="Paris",
            zipcode="75000",
            telephone="0100000000",
            email=f"{empid}@example.com",
            admidate=date(2020, 1, 1),
            salary=Decimal("1000.00"),
            dept=department,
        )
    crews = seed_crews()

    generate_flights(date(2030, 1, 1), 3, crews)

    assert Shift.objects.count() == 12
    assert Flight.objects.count() == 24

    existing = Flight.objects.get(flightnum="CB2204", flightdate=date(2030, 1, 1))
    existing.totbagga = 17
    existing.save(update_fields=["totbagga"])
    generate_flights(date(2030, 1, 1), 3, crews)

    assert Shift.objects.count() == 12
    assert Flight.objects.count() == 24
    existing.refresh_from_db()
    assert existing.totbagga == 17
