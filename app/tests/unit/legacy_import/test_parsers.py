from datetime import date
from pathlib import Path

import pytest

from legacy_import.parsers import (
    parse_employee_json,
    parse_legacy_date,
    parse_legacy_time,
    parse_passenger_xml,
)

LEGACY_ROOT = Path(__file__).parent / "fixtures" / "legacy_root"


def test_parse_employee_json_normalizes_legacy_types():
    rows = parse_employee_json(LEGACY_ROOT / "COB-PROG/EMPLO-INSERT/EMPLOYEE-LIST.json")

    assert rows[0]["empid"] == "10000006"
    assert rows[0]["admidate"] == date(2020, 2, 3)
    assert rows[0]["telephone"] == "612345678"
    assert rows[0]["zipcode"] == "75000"


def test_parse_passenger_xml_preserves_utf8_and_trims_values():
    rows = parse_passenger_xml(LEGACY_ROOT / "COB-PROG/PASSENGER-INSERT/PASSENGER1.xml")

    assert rows[0]["firstname"] == "René"
    assert rows[0]["lastname"] == "Été"
    assert rows[0]["address"] == "1 rue A"
    assert rows[0]["telephone"] == "0612345678"


def test_parse_db2_dates_and_times_are_format_explicit():
    assert parse_legacy_date("09/12/2026", "us") == date(2026, 9, 12)
    assert parse_legacy_date("2026-09-12", "iso") == date(2026, 9, 12)
    assert parse_legacy_time("08:30").second == 0
    assert parse_legacy_time("08:30:45").second == 45
    with pytest.raises(ValueError):
        parse_legacy_date("09/12/2026", "iso")
