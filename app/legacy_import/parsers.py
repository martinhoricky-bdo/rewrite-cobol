"""Parsers read EMPINSRT/SUINSRT EMPLOYEE-LIST.json and PASSENG/SUXML PASSENGER1..8.xml
exports.
"""

import json
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree


def parse_legacy_date(value: str, fmt: str = "iso") -> date:
    """Parse a DB2 DEL date using the explicitly selected export format."""
    formats = {"iso": "%Y-%m-%d", "us": "%m/%d/%Y"}
    try:
        pattern = formats[fmt]
    except KeyError as exc:
        raise ValueError(f"unsupported date format: {fmt}") from exc
    return datetime.strptime(value.strip(), pattern).date()


def parse_legacy_time(value: str) -> time:
    """Parse DB2 times with or without seconds."""
    value = value.strip()
    for pattern in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(value, pattern).time()
        except ValueError:
            pass
    raise ValueError(f"invalid time: {value}")


def parse_employee_json(path: Path) -> list[dict]:
    """Implement parse_employee_json behavior for the EMPINSRT, SUINSRT, PASSENG, SUXML,
    and DB2 export formats.
    """
    rows = json.loads(path.read_text(encoding="utf-8"))["ws-emplist"]["ws-emplist-table"]
    result = []
    for source in rows:
        row = dict(source)
        row["empid"] = str(10_000_000 + int(row["empid"]))
        row["admidate"] = datetime.strptime(
            row.pop("admidate", row.pop("admindate", None)), "%Y/%m/%d"
        ).date()
        row["salary"] = Decimal(str(row["salary"]))
        row["zipcode"] = str(row["zipcode"])
        row["telephone"] = str(row["telephone"])
        result.append(row)
    return result


def parse_passenger_xml(path: Path) -> list[dict]:
    """Implement parse_passenger_xml behavior for the EMPINSRT, SUINSRT, PASSENG, SUXML,
    and DB2 export formats.
    """
    names = {
        "FIRSTNAME": "firstname",
        "LASTNAME": "lastname",
        "ADDRE": "address",
        "CITY": "city",
        "COUNTRY": "country",
        "ZIPCODE": "zipcode",
        "TELEPHONE": "telephone",
        "EMAIL": "email",
    }
    return [
        {target: (element.findtext(source) or "").strip() for source, target in names.items()}
        for element in ElementTree.parse(path).getroot().findall("PASSENGER-TABLE")
    ]
