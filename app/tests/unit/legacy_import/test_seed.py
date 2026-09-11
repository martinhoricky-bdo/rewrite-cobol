from io import StringIO
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from accounts.models import Department, Employee
from fleet.models import Airplane, Airport
from operations.models import Crew, Flight, Shift
from sales.models import Buy, Passenger, Ticket
from sales.services import next_ticket_id

pytestmark = pytest.mark.django_db
FIXTURE_ROOT = Path(__file__).parent / "fixtures/legacy_root"
EXPECTED_COUNTS = (9, 9, 10, 11, 3, 1, 32, 64, 0, 0)


def counts():
    models = (Department, Airport, Airplane, Employee, Passenger, Crew, Shift, Flight, Buy, Ticket)
    return tuple(model.objects.count() for model in models)


def run_seed(*, flush=False):
    call_command(
        "seed_demo",
        flush=flush,
        from_date="2030-01-01",
        days=2,
        stdout=StringIO(),
    )


def assert_seeded_data(client):
    assert counts() == EXPECTED_COUNTS
    assert Department.objects.get(pk=1).manager_id == "10000029"
    assert Department.objects.get(pk=7).manager_id is None
    assert Passenger.objects.get(pk=3).firstname == "MAXIME"
    assert Passenger.objects.get(pk=3).lastname == "DUPRAT"
    assert next_ticket_id() == "CB00000001"
    assert client.login(username="10000006", password="kxXRk7GIHw")
    assert not get_user_model().objects.get(username="10000031").is_active


def test_seed_is_idempotent_and_flush_recreates_data(settings, client):
    settings.LEGACY_ROOT = FIXTURE_ROOT

    run_seed()
    assert_seeded_data(client)

    run_seed()
    assert_seeded_data(client)

    run_seed(flush=True)
    assert_seeded_data(client)
