from datetime import date
from pathlib import Path

from legacy_import.parsers import parse_employee_json, parse_passenger_xml

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_employee_json_normalizes_legacy_types():
    rows = parse_employee_json(FIXTURES / "EMPLOYEE-LIST.json")

    assert rows[0]["empid"] == "10000006"
    assert rows[0]["admidate"] == date(2020, 2, 3)
    assert rows[0]["telephone"] == "612345678"
    assert rows[0]["zipcode"] == "75000"


def test_parse_passenger_xml_preserves_utf8_and_trims_values():
    rows = parse_passenger_xml(FIXTURES / "PASSENGER1.xml")

    assert rows[0]["firstname"] == "René"
    assert rows[0]["lastname"] == "Été"
    assert rows[0]["address"] == "1 rue A"
    assert rows[0]["telephone"] == "0612345678"
