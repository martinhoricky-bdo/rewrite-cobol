import logging
from datetime import date, time, timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.db import connection

from accounts.models import Department, Employee
from accounts.services import ensure_user_for_employee
from fleet.models import Airplane, Airport
from operations.models import Crew, Flight, Shift
from sales.models import Buy, Passenger, Ticket
from sales.services import reset_ticket_sequence

from .data import (
    AIRPLANES,
    AIRPORTS,
    CREWS,
    DEPARTMENTS,
    EXTRA_EMPLOYEES,
    FLIGHT_PATTERNS,
    MANAGERS,
    PRICE,
)
from .parsers import parse_employee_json, parse_passenger_xml

logger = logging.getLogger("cobol_airlines")
User = get_user_model()
CREW_FIELDS = (
    "commander",
    "copilote",
    "fachief",
    "fliattendant1",
    "fliattendant2",
    "fliattendant3",
)


def seed_reference_data() -> None:
    for pk, name in DEPARTMENTS:
        Department.objects.update_or_create(deptid=pk, defaults={"name": name})
    for values in AIRPORTS:
        Airport.objects.update_or_create(
            airportid=values[0],
            defaults=dict(
                zip(("name", "address", "city", "country", "zipcode"), values[1:], strict=True)
            ),
        )
    for values in AIRPLANES:
        Airplane.objects.update_or_create(
            airplaneid=values[0],
            defaults=dict(zip(("type", "numseats", "totalfuel"), values[1:], strict=True)),
        )


def _employee(values: dict, password: str | None) -> Employee:
    empid = values.pop("empid")
    values["dept_id"] = values.pop("deptid")
    employee, _ = Employee.objects.update_or_create(empid=empid, defaults=values)
    user = ensure_user_for_employee(employee)
    for field in ("first_name", "last_name", "email"):
        user_value = values[
            {"first_name": "firstname", "last_name": "lastname", "email": "email"}[field]
        ]
        setattr(user, field, user_value)
    user.is_active = password is not None
    if password and not user.has_usable_password():
        user.set_password(password) if password else user.set_unusable_password()
    user.save()
    return employee


def seed_employees(path: Path) -> None:
    for row in parse_employee_json(path):
        password = row.pop("passw")
        _employee(row, password)
    fields = (
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
    )
    for values in EXTRA_EMPLOYEES:
        _employee(dict(zip(fields, values, strict=True)), None)
    for deptid, empid in MANAGERS.items():
        manager = Employee.objects.filter(pk=empid).first()
        if manager:
            Department.objects.filter(pk=deptid).update(manager=manager)
        else:
            logger.warning("Skipping manager %s for department %s: employee missing", empid, deptid)


def _reset_passenger_sequence() -> None:
    table = connection.ops.quote_name(Passenger._meta.db_table)
    with connection.cursor() as cursor:
        if connection.vendor == "postgresql":
            cursor.execute(
                "SELECT setval(pg_get_serial_sequence(%s, 'clientid'), "
                "COALESCE(MAX(clientid), 0) + 1, false) FROM passengers",
                [Passenger._meta.db_table],
            )
        elif connection.vendor == "sqlite":
            cursor.execute(
                "DELETE FROM sqlite_sequence WHERE name = %s", [Passenger._meta.db_table]
            )
            cursor.execute(
                f"INSERT INTO sqlite_sequence(name, seq) "
                f"SELECT %s, COALESCE(MAX(clientid), 0) FROM {table}",
                [Passenger._meta.db_table],
            )


def seed_passengers(paths: list[Path]) -> Passenger:
    rows = [row for path in paths for row in parse_passenger_xml(path)]
    for clientid, row in enumerate(rows, 1):
        row.update(firstname=row["firstname"].upper(), lastname=row["lastname"].upper())
        Passenger.objects.update_or_create(clientid=clientid, defaults=row)
    final_id = len(rows) + 1
    maxime, _ = Passenger.objects.update_or_create(
        clientid=final_id,
        defaults={
            "firstname": "MAXIME",
            "lastname": "DUPRAT",
            "address": "23 rue de New York",
            "city": "Rocherchouart",
            "country": "France",
            "zipcode": "87600",
            "telephone": "0666666666",
            "email": "maxime_duprat@gmail.com",
        },
    )
    _reset_passenger_sequence()
    return maxime


def seed_crews() -> dict[int, Crew]:
    result = {}
    for index, member_ids in enumerate(CREWS):
        members = {
            employee.empid: employee for employee in Employee.objects.filter(empid__in=member_ids)
        }
        if len(members) != 6:
            logger.warning("Skipping crew %s: employee missing", index + 1)
            continue
        lookup = {
            f"{field}_id": empid for field, empid in zip(CREW_FIELDS, member_ids, strict=True)
        }
        crew, _ = Crew.objects.get_or_create(**lookup)
        result[index] = crew
    return result


def generate_flights(start: date, days: int, crews: dict[int, Crew] | None = None) -> None:
    crews = (
        crews
        if crews is not None
        else {
            index: crew
            for index, ids in enumerate(CREWS)
            if (
                crew := Crew.objects.filter(
                    **{f"{field}_id": empid for field, empid in zip(CREW_FIELDS, ids, strict=True)}
                ).first()
            )
        }
    )
    patterns = [(pattern, crews.get(pattern[-1])) for pattern in FLIGHT_PATTERNS]
    for pattern, crew in patterns:
        if not crew:
            logger.warning("Skipping flight pattern %s: crew missing", pattern[0])
    for offset in range(days):
        day = start + timedelta(days=offset)
        shifts = {
            index: Shift.objects.get_or_create(
                shiftdate=day, crew=crew, defaults={"begintime": time(9), "endtime": time(21)}
            )[0]
            for index, crew in crews.items()
        }
        for pattern, crew in patterns:
            if not crew:
                continue
            number, dep, arr, departure, arrival, airplaneid, crew_index = pattern
            airplane = Airplane.objects.get(pk=airplaneid)
            Flight.objects.get_or_create(
                flightnum=number,
                flightdate=day,
                defaults={
                    "deptime": time.fromisoformat(departure),
                    "arrtime": time.fromisoformat(arrival),
                    "totpass": airplane.numseats,
                    "totbagga": 0,
                    "shift": shifts[crew_index],
                    "airplane": airplane,
                    "airportdep_id": dep,
                    "airportarr_id": arr,
                    "price": PRICE,
                },
            )


def seed_reference_purchase(client: Passenger) -> None:
    flight = Flight.objects.filter(flightnum="CB2204", flightdate=date(2022, 9, 1)).first()
    employee = Employee.objects.filter(pk="10000006").first()
    if not flight or not employee:
        logger.warning("Skipping reference purchase: flight or employee missing")
        reset_ticket_sequence()
        return
    buy, _ = Buy.objects.get_or_create(
        buydate=date(2022, 9, 8),
        buytime=time(10, 3),
        emp=employee,
        client=client,
        defaults={"price": PRICE},
    )
    Ticket.objects.update_or_create(
        ticketid="CB00000001",
        defaults={"buy": buy, "client": client, "flight": flight, "seat": "B04"},
    )
    reset_ticket_sequence()


def flush_seed_data() -> None:
    for model in (Ticket, Buy, Flight, Shift, Crew, Passenger):
        model.objects.all().delete()
    user_ids = list(Employee.objects.exclude(user=None).values_list("user_id", flat=True))
    Department.objects.update(manager=None)
    Employee.objects.all().delete()
    User.objects.filter(pk__in=user_ids).delete()
    Department.objects.all().delete()
    Airplane.objects.all().delete()
    Airport.objects.all().delete()
