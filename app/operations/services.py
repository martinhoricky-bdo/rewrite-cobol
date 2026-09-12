from dataclasses import dataclass
from datetime import date, time, timedelta

from django.db import transaction
from django.db.models import Count, F, IntegerField, OuterRef, Q, QuerySet, Subquery, Value
from django.db.models.functions import Coalesce

from fleet.models import Airplane
from sales.models import Ticket

from .models import Crew, Flight, Shift


@dataclass(frozen=True)
class GenerateResult:
    created: int
    skipped: int


@transaction.atomic
def generate_flights(
    template: Flight, date_from: date, date_to: date, weekdays: set[int]
) -> GenerateResult:
    """Clone a flight over an inclusive date range, preserving its crew."""
    created = skipped = 0
    day = date_from
    while day <= date_to:
        if day.weekday() not in weekdays:
            day += timedelta(days=1)
            continue
        if Flight.objects.filter(flightnum=template.flightnum, flightdate=day).exists():
            skipped += 1
            day += timedelta(days=1)
            continue
        shift = Shift.objects.filter(shiftdate=day, crew=template.shift.crew).first()
        if shift is None:
            shift = Shift.objects.create(
                shiftdate=day,
                crew=template.shift.crew,
                begintime=template.shift.begintime,
                endtime=template.shift.endtime,
            )
        Flight.objects.create(
            flightdate=day,
            deptime=template.deptime,
            arrtime=template.arrtime,
            totpass=template.totpass,
            totbagga=template.totbagga,
            flightnum=template.flightnum,
            shift=shift,
            airplane=template.airplane,
            airportdep=template.airportdep,
            airportarr=template.airportarr,
            price=template.price,
        )
        created += 1
        day += timedelta(days=1)
    return GenerateResult(created=created, skipped=skipped)


def generate_seed_flights(start: date, days: int, crews: dict[int, Crew]) -> None:
    """Create the legacy demo flight patterns used by ``seed_demo``."""
    from legacy_import.data import FLIGHT_PATTERNS, PRICE

    patterns = [(pattern, crews.get(pattern[-1])) for pattern in FLIGHT_PATTERNS]
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


def free_seats_subquery() -> Subquery:
    ticket_counts = (
        Ticket.objects.filter(flight_id=OuterRef("pk"))
        .values("flight_id")
        .annotate(count=Count("pk"))
        .values("count")
    )
    return Subquery(ticket_counts, output_field=IntegerField())


def search_flights(
    *,
    flightnum: str | None,
    flightdate: date | None,
    airportdep: str | None,
    airportarr: str | None,
    today: date,
) -> QuerySet[Flight]:
    filters = {}
    if flightnum and (flightnum := flightnum.strip()):
        filters["flightnum__iexact"] = flightnum
    if airportdep and (airportdep := airportdep.strip()):
        filters["airportdep__airportid__iexact"] = airportdep
    if airportarr and (airportarr := airportarr.strip()):
        filters["airportarr__airportid__iexact"] = airportarr
    if flightdate is None:
        filters["flightdate__gte"] = today
    else:
        filters["flightdate"] = flightdate

    return (
        Flight.objects.filter(**filters)
        .select_related("airplane", "airportdep", "airportarr")
        .annotate(sold=Coalesce(free_seats_subquery(), Value(0)))
        .annotate(free_seats=F("airplane__numseats") - F("sold"))
        .order_by("flightdate", "deptime", "flightnum")
    )


def schedule_flights(
    *, date_from: date, date_to: date, flightnum: str = "", airport: str = ""
) -> QuerySet[Flight]:
    filters = Q(flightdate__range=(date_from, date_to))
    if flightnum.strip():
        filters &= Q(flightnum__iexact=flightnum.strip())
    if airport.strip():
        code = airport.strip()
        filters &= Q(airportdep__airportid__iexact=code) | Q(airportarr__airportid__iexact=code)
    return (
        Flight.objects.filter(filters)
        .select_related("airplane", "airportdep", "airportarr", "shift__crew")
        .annotate(sold=Coalesce(free_seats_subquery(), Value(0)))
        .order_by("flightdate", "deptime", "flightnum")
    )
