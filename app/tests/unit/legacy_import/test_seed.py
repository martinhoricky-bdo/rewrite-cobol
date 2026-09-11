from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from accounts.models import Department, Employee
from fleet.models import Airplane, Airport
from operations.models import Crew, Flight, Shift
from sales.models import Buy, Passenger, Ticket
from sales.services import next_ticket_id

pytestmark = pytest.mark.django_db(transaction=True)
LEGACY_ROOT = Path(__file__).parent / "fixtures" / "legacy_root"
User = get_user_model()


def counts():
    return {
        "dept": Department.objects.count(),
        "airport": Airport.objects.count(),
        "airplane": Airplane.objects.count(),
        "emplo": Employee.objects.count(),
        "passengers": Passenger.objects.count(),
        "crew": Crew.objects.count(),
        "shift": Shift.objects.count(),
        "flight": Flight.objects.count(),
        "buy": Buy.objects.count(),
        "ticket": Ticket.objects.count(),
    }


def test_seed_demo_with_small_legacy_fixture_is_idempotent(settings, client, caplog):
    settings.LEGACY_ROOT = LEGACY_ROOT
    expected = {
        "dept": 9,
        "airport": 9,
        "airplane": 10,
        "emplo": 11,
        "passengers": 3,
        "crew": 1,
        "shift": 32,
        "flight": 64,
        "buy": 0,
        "ticket": 0,
    }

    call_command("seed_demo", from_date="2030-01-01", days=2)

    assert counts() == expected
    assert Department.objects.get(pk=1).manager_id == "10000029"
    assert Department.objects.get(pk=7).manager_id is None
    assert Passenger.objects.get(pk=3).firstname == "MAXIME"
    assert next_ticket_id() == "CB00000001"
    assert client.login(username="10000006", password="kxXRk7GIHw")
    assert not User.objects.get(username="10000031").is_active
    assert "Skipping manager 10000019 for department 7" in caplog.text
    assert "Skipping reference purchase" in caplog.text

    call_command("seed_demo", from_date="2030-01-01", days=2)

    assert counts() == expected
    assert client.login(username="10000006", password="kxXRk7GIHw")

    call_command("seed_demo", flush=True, from_date="2030-01-01", days=2)

    assert counts() == expected
    assert client.login(username="10000006", password="kxXRk7GIHw")
