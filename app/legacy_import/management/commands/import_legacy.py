import csv
import json
from collections.abc import Callable
from decimal import Decimal, DecimalException
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, connection, transaction

from accounts.models import Department, Employee
from fleet.models import Airplane, Airport
from legacy_import.parsers import parse_legacy_date, parse_legacy_time
from operations.models import Crew, Flight, Shift
from sales.models import Buy, Passenger, Ticket
from sales.services import reset_ticket_sequence

User = get_user_model()

COLUMNS = {
    "AIRPORT": ("airportid", "name", "address", "city", "country", "zipcode"),
    "AIRPLANE": ("airplaneid", "type", "numseats", "totalfuel"),
    "DEPT": ("deptid", "name", "manager"),
    "EMPLO": (
        "empid",
        "firstname",
        "lastname",
        "addre",
        "city",
        "zipcode",
        "telephone",
        "email",
        "admidate",
        "salary",
        "deptid",
    ),
    "PASSENGERS": (
        "clientid",
        "firstname",
        "lastname",
        "address",
        "city",
        "country",
        "zipcode",
        "telephone",
        "email",
    ),
    "CREW": (
        "crewid",
        "commander",
        "copilote",
        "fachief",
        "fliattendant1",
        "fliattendant2",
        "fliattendant3",
    ),
    "SHIFT": ("shiftid", "shiftdate", "begintime", "endtime", "crewid"),
    "FLIGHT": (
        "flightid",
        "flightdate",
        "deptime",
        "arrtime",
        "totpass",
        "totbagga",
        "flightnum",
        "shiftid",
        "airplaneid",
        "airportdep",
        "airportarr",
    ),
    "BUY": ("buyid", "buydate", "buytime", "price", "empid", "clientid"),
    "TICKET": ("ticketid", "buyid", "clientid", "flightid", "seat"),
}


class Command(BaseCommand):
    help = "Import a DB2 EXPORT OF DEL directory."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--dir", required=True, type=Path)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--report", type=Path)
        parser.add_argument("--date-format", choices=("iso", "us"), default="iso")

    def handle(self, *args, **options) -> None:
        directory = options["dir"]
        if not directory.is_dir():
            raise CommandError(f"Import directory not found: {directory}")
        self.date_format = options["date_format"]
        self.report = {
            "tables": {name: {"inserted": 0, "updated": 0, "skipped": 0} for name in COLUMNS},
            "errors": [],
            "created_accounts": [],
            "dry_run": options["dry_run"],
        }
        with transaction.atomic():
            self._run(directory)
            self._reset_sequences()
            if options["dry_run"]:
                transaction.set_rollback(True)
        if options["report"]:
            options["report"].parent.mkdir(parents=True, exist_ok=True)
            options["report"].write_text(json.dumps(self.report, indent=2), encoding="utf-8")
        self._print_summary()

    def _rows(self, directory: Path, table: str):
        path = directory / f"{table}.csv"
        if not path.exists():
            self.stderr.write(self.style.WARNING(f"Missing {path.name}; skipping"))
            return []
        with path.open(newline="", encoding="utf-8-sig") as stream:
            raw = list(csv.reader(stream))
        columns = COLUMNS[table]
        if raw and tuple(value.strip().lower() for value in raw[0]) == columns:
            raw = raw[1:]
            first_line = 2
        else:
            first_line = 1
        result = []
        for number, values in enumerate(raw, first_line):
            if len(values) != len(columns):
                self._error(table, number, f"expected {len(columns)} columns, got {len(values)}")
                continue
            result.append((number, dict(zip(columns, (v.strip() for v in values), strict=True))))
        return result

    def _import(self, directory: Path, table: str, callback: Callable) -> list[dict]:
        rows = []
        for number, row in self._rows(directory, table):
            try:
                with transaction.atomic():
                    created = callback(row)
            except (ValueError, TypeError, DecimalException, IntegrityError) as exc:
                self._error(table, number, str(exc))
            else:
                self.report["tables"][table]["inserted" if created else "updated"] += 1
                rows.append((number, row))
        return rows

    def _error(self, table: str, row: int, error: str) -> None:
        self.report["tables"][table]["skipped"] += 1
        self.report["errors"].append({"table": table, "row": row, "error": error})

    @staticmethod
    def _require(model, value, label: str):
        if not model.objects.filter(pk=value).exists():
            raise ValueError(f"{label} {value} not found")
        return value

    def _run(self, directory: Path) -> None:
        self._import(directory, "AIRPORT", self._airport)
        self._import(directory, "AIRPLANE", self._airplane)
        departments = self._import(directory, "DEPT", self._department)
        self._import(directory, "EMPLO", self._employee)
        self._managers(departments)
        self._import(directory, "PASSENGERS", self._passenger)
        self._import(directory, "CREW", self._crew)
        self._import(directory, "SHIFT", self._shift)
        self._import(directory, "FLIGHT", self._flight)
        self._import(directory, "BUY", self._buy)
        self._import(directory, "TICKET", self._ticket)

    def _airport(self, r):
        pk = r.pop("airportid").upper()
        r["country"] = r["country"] or ""
        return Airport.objects.update_or_create(airportid=pk, defaults=r)[1]

    def _airplane(self, r):
        pk = r.pop("airplaneid").upper()
        r.update(numseats=int(r["numseats"]), totalfuel=int(r["totalfuel"]))
        return Airplane.objects.update_or_create(airplaneid=pk, defaults=r)[1]

    def _department(self, r):
        return Department.objects.update_or_create(
            deptid=int(r["deptid"]), defaults={"name": r["name"]}
        )[1]

    def _employee(self, r):
        if len(r["telephone"]) > 20:
            raise ValueError("telephone exceeds 20 characters")
        deptid = self._require(Department, int(r.pop("deptid")), "dept")
        empid = r.pop("empid")
        r.update(
            admidate=parse_legacy_date(r["admidate"], self.date_format),
            salary=Decimal(r["salary"]),
            dept_id=deptid,
        )
        user, user_created = User.objects.get_or_create(
            username=empid, defaults={"is_active": False}
        )
        if user_created:
            user.set_unusable_password()
            user.save(update_fields=["password"])
            self.report["created_accounts"].append(empid)
        r["user"] = user
        return Employee.objects.update_or_create(empid=empid, defaults=r)[1]

    def _managers(self, rows):
        for number, r in rows:
            manager = r["manager"]
            if not manager:
                Department.objects.filter(pk=int(r["deptid"])).update(manager=None)
            elif Employee.objects.filter(pk=manager).exists():
                Department.objects.filter(pk=int(r["deptid"])).update(manager_id=manager)
            else:
                self._error("DEPT", number, f"emplo {manager} not found")

    def _passenger(self, r):
        pk = int(r.pop("clientid"))
        r["country"] = r["country"] or ""
        return Passenger.objects.update_or_create(clientid=pk, defaults=r)[1]

    def _crew(self, r):
        pk = int(r.pop("crewid"))
        defaults = {}
        for field, empid in r.items():
            defaults[f"{field}_id"] = self._require(Employee, empid, "emplo")
        return Crew.objects.update_or_create(crewid=pk, defaults=defaults)[1]

    def _shift(self, r):
        pk = int(r.pop("shiftid"))
        crewid = self._require(Crew, int(r.pop("crewid")), "crew")
        r.update(
            shiftdate=parse_legacy_date(r["shiftdate"], self.date_format),
            begintime=parse_legacy_time(r["begintime"]),
            endtime=parse_legacy_time(r["endtime"]),
            crew_id=crewid,
        )
        return Shift.objects.update_or_create(shiftid=pk, defaults=r)[1]

    def _flight(self, r):
        pk = int(r.pop("flightid"))
        defaults = {
            "flightdate": parse_legacy_date(r["flightdate"], self.date_format),
            "deptime": parse_legacy_time(r["deptime"]),
            "arrtime": parse_legacy_time(r["arrtime"]),
            "totpass": int(r["totpass"]),
            "totbagga": int(r["totbagga"]),
            "flightnum": r["flightnum"].upper(),
            "price": Decimal("120.99"),
        }
        for field, model, label in (
            ("shiftid", Shift, "shift"),
            ("airplaneid", Airplane, "airplane"),
            ("airportdep", Airport, "airport"),
            ("airportarr", Airport, "airport"),
        ):
            value = int(r[field]) if field == "shiftid" else r[field].upper()
            defaults[
                {"shiftid": "shift_id", "airplaneid": "airplane_id"}.get(field, f"{field}_id")
            ] = self._require(model, value, label)
        return Flight.objects.update_or_create(flightid=pk, defaults=defaults)[1]

    def _buy(self, r):
        pk = int(r.pop("buyid"))
        defaults = {
            "buydate": parse_legacy_date(r["buydate"], self.date_format),
            "buytime": parse_legacy_time(r["buytime"]),
            "price": Decimal(r["price"]),
            "emp_id": self._require(Employee, r["empid"], "emplo"),
            "client_id": self._require(Passenger, int(r["clientid"]), "passenger"),
        }
        return Buy.objects.update_or_create(buyid=pk, defaults=defaults)[1]

    def _ticket(self, r):
        pk = r.pop("ticketid").upper()
        seat = r["seat"].upper()
        if len(seat) == 2 and seat[1].isdigit():
            seat = f"{seat[0]}0{seat[1]}"
        defaults = {
            "buy_id": self._require(Buy, int(r["buyid"]), "buy"),
            "client_id": self._require(Passenger, int(r["clientid"]), "passenger"),
            "flight_id": self._require(Flight, int(r["flightid"]), "flight"),
            "seat": seat,
        }
        return Ticket.objects.update_or_create(ticketid=pk, defaults=defaults)[1]

    def _reset_sequences(self):
        if connection.vendor == "postgresql":
            with connection.cursor() as cursor:
                for model, column in (
                    (Passenger, "clientid"),
                    (Crew, "crewid"),
                    (Shift, "shiftid"),
                    (Flight, "flightid"),
                    (Buy, "buyid"),
                ):
                    table = connection.ops.quote_name(model._meta.db_table)
                    cursor.execute(
                        "SELECT setval(pg_get_serial_sequence(%s, %s), "
                        f"COALESCE(MAX({column}), 0) + 1, false) FROM {table}",
                        [model._meta.db_table, column],
                    )
        reset_ticket_sequence()

    def _print_summary(self):
        self.stdout.write("TABLE       INSERTED UPDATED SKIPPED")
        for table, counts in self.report["tables"].items():
            self.stdout.write(
                f"{table:<12}{counts['inserted']:<9}{counts['updated']:<8}{counts['skipped']}"
            )
        self.stdout.write(self.style.SUCCESS("Legacy import completed"))
