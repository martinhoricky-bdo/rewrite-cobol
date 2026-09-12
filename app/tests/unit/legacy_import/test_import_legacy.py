import json
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from accounts.models import Employee
from fleet.models import Airport
from operations.models import Crew, Flight
from sales.models import Passenger, Ticket
from sales.services import next_ticket_id

FIXTURES = Path(__file__).parent / "fixtures/db2_export"


@pytest.mark.django_db(transaction=True)
def test_import_normalizes_reports_and_resets_sequences(tmp_path):
    report_path = tmp_path / "report.json"
    call_command("import_legacy", dir=FIXTURES, report=report_path)

    report = json.loads(report_path.read_text())
    assert Airport.objects.filter(pk="CDG").exists()
    assert Flight.objects.get(pk=5).flightnum == "CB1001"
    assert Passenger.objects.get(pk=8).country == ""
    assert Ticket.objects.get(pk="CB00000010").seat == "B04"
    assert Crew.objects.count() == 2
    assert {error["table"] for error in report["errors"]} >= {"CREW", "SHIFT"}
    assert report["created_accounts"] == ["10000001", "10000002", "10000003"]
    user = get_user_model().objects.get(username="10000001")
    assert not user.is_active and not user.has_usable_password()
    assert Employee.objects.get(pk="10000001").user == user
    assert next_ticket_id() == "CB00000011"
    assert (
        Passenger.objects.create(
            firstname="N",
            lastname="N",
            address="A",
            city="C",
            country="",
            zipcode="Z",
            telephone="1",
            email="n@example.com",
        ).pk
        == 11
    )


@pytest.mark.django_db(transaction=True)
def test_import_is_idempotent(tmp_path):
    call_command("import_legacy", dir=FIXTURES)
    report_path = tmp_path / "second.json"
    call_command("import_legacy", dir=FIXTURES, report=report_path)
    report = json.loads(report_path.read_text())
    assert sum(item["inserted"] for item in report["tables"].values()) == 0
    assert sum(item["updated"] for item in report["tables"].values()) > 0


@pytest.mark.django_db(transaction=True)
def test_dry_run_writes_report_without_data(tmp_path):
    report_path = tmp_path / "dry.json"
    call_command("import_legacy", dir=FIXTURES, dry_run=True, report=report_path)
    assert report_path.exists()
    assert json.loads(report_path.read_text())["dry_run"] is True
    assert not Airport.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_us_date_format_imports_separate_export_fixture():
    fixtures = Path(__file__).parent / "fixtures/db2_export_us"
    call_command("import_legacy", dir=fixtures, date_format="us")
    assert Employee.objects.get(pk="10000001").admidate.isoformat() == "2020-01-01"
