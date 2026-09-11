import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree


def parse_employee_json(path: Path) -> list[dict]:
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
