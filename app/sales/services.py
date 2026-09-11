from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal

from django.db import connection
from django.db.models import F, QuerySet, Value
from django.db.models.functions import Coalesce

from core.messages import E_SEL_05, E_SEL_06, E_SEL_07, E_SEL_08
from operations.models import Flight
from operations.services import free_seats_subquery

from .models import Passenger, Ticket

LEGACY_MONTHS = (
    "JAN",
    "FEB",
    "MAR",
    "APR",
    "MAY",
    "JUN",
    "JUL",
    "AUG",
    "SEP",
    "OCT",
    "NOV",
    "DEC",
)

SESSION_KEY = "sale_quote"


class SaleError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class SaleQuote:
    flight_id: int
    flightnum: str
    flightdate: date
    deptime: time
    arrtime: time
    airportdep: str
    airportarr: str
    client_id: int
    client_name: str
    count: int
    unit_price: Decimal
    total_price: Decimal
    free_seats: int

    def to_session(self) -> dict:
        return {
            "flight_id": self.flight_id,
            "flightnum": self.flightnum,
            "flightdate": self.flightdate.isoformat(),
            "deptime": self.deptime.strftime("%H:%M"),
            "arrtime": self.arrtime.strftime("%H:%M"),
            "airportdep": self.airportdep,
            "airportarr": self.airportarr,
            "client_id": self.client_id,
            "client_name": self.client_name,
            "count": self.count,
            "unit_price": str(self.unit_price),
            "total_price": str(self.total_price),
            "free_seats": self.free_seats,
        }

    @classmethod
    def from_session(cls, data) -> "SaleQuote":
        return cls(
            flight_id=int(data["flight_id"]),
            flightnum=str(data["flightnum"]),
            flightdate=date.fromisoformat(data["flightdate"]),
            deptime=time.fromisoformat(data["deptime"]),
            arrtime=time.fromisoformat(data["arrtime"]),
            airportdep=str(data["airportdep"]),
            airportarr=str(data["airportarr"]),
            client_id=int(data["client_id"]),
            client_name=str(data["client_name"]),
            count=int(data["count"]),
            unit_price=Decimal(data["unit_price"]),
            total_price=Decimal(data["total_price"]),
            free_seats=int(data["free_seats"]),
        )


def quote_sale(
    *, clientid: int, flightnum: str, flightdate: date, count: int, today: date
) -> SaleQuote:
    try:
        passenger = Passenger.objects.get(pk=clientid)
    except Passenger.DoesNotExist as exc:
        raise SaleError("E_SEL_05", E_SEL_05) from exc

    try:
        flight = (
            Flight.objects.select_related("airplane", "airportdep", "airportarr")
            .annotate(sold=Coalesce(free_seats_subquery(), Value(0)))
            .annotate(free_seats=F("airplane__numseats") - F("sold"))
            .get(flightnum__iexact=flightnum, flightdate=flightdate)
        )
    except Flight.DoesNotExist as exc:
        raise SaleError("E_SEL_06", E_SEL_06) from exc

    if flightdate < today:
        raise SaleError("E_SEL_07", E_SEL_07)
    if flight.free_seats < count:
        raise SaleError("E_SEL_08", E_SEL_08.format(n=flight.free_seats))

    unit_price = flight.price.quantize(Decimal("0.01"))
    total_price = (unit_price * count).quantize(Decimal("0.01"))
    return SaleQuote(
        flight_id=flight.pk,
        flightnum=flight.flightnum,
        flightdate=flight.flightdate,
        deptime=flight.deptime,
        arrtime=flight.arrtime,
        airportdep=flight.airportdep_id,
        airportarr=flight.airportarr_id,
        client_id=passenger.pk,
        client_name=passenger.full_name,
        count=count,
        unit_price=unit_price,
        total_price=total_price,
        free_seats=flight.free_seats,
    )


def filter_passengers(
    *,
    clientid: int | None = None,
    lastname: str | None = None,
    firstname: str | None = None,
    email: str | None = None,
) -> QuerySet[Passenger]:
    passengers = Passenger.objects.all()
    if clientid is not None:
        passengers = passengers.filter(clientid=clientid)
    if lastname:
        passengers = passengers.filter(lastname__istartswith=lastname)
    if firstname:
        passengers = passengers.filter(firstname__istartswith=firstname)
    if email:
        passengers = passengers.filter(email__icontains=email)
    return passengers.order_by("lastname", "firstname", "clientid")


def legacy_date(d: date) -> str:
    return f"{d.day:02d}{LEGACY_MONTHS[d.month - 1]}{d.year:04d}"


def boarding_pass_context(ticket: Ticket) -> dict[str, str]:
    flight = ticket.flight
    passenger = ticket.client
    dep_code = flight.airportdep_id
    arr_code = flight.airportarr_id
    return {
        "passenger_name": f"{passenger.firstname} {passenger.lastname}".upper(),
        "seat": ticket.seat,
        "flightnum": flight.flightnum,
        "dep_code": dep_code,
        "arr_code": arr_code,
        "dep_city": f"{flight.airportdep.city}-{dep_code}".upper(),
        "arr_city": f"{flight.airportarr.city}-{arr_code}".upper(),
        "flightdate_iso": flight.flightdate.isoformat(),
        "flightdate_legacy": legacy_date(flight.flightdate),
        "deptime": flight.deptime.strftime("%H:%M"),
        "ticketid": ticket.ticketid,
    }


def search_tickets(
    *,
    ticketid: str | None = None,
    clientid: int | None = None,
    firstname: str | None = None,
    lastname: str | None = None,
    flightnum: str | None = None,
    flightdate: date | None = None,
) -> QuerySet[Ticket]:
    tickets = Ticket.objects.select_related(
        "client", "flight", "flight__airportdep", "flight__airportarr", "buy"
    )
    if ticketid:
        tickets = tickets.filter(ticketid=ticketid.upper())
    elif clientid:
        tickets = tickets.filter(client_id=clientid)
        if flightnum:
            tickets = tickets.filter(flight__flightnum__iexact=flightnum)
        if flightdate:
            tickets = tickets.filter(flight__flightdate=flightdate)
    elif firstname and lastname:
        tickets = tickets.filter(
            client__firstname__iexact=firstname, client__lastname__iexact=lastname
        )
        if flightnum:
            tickets = tickets.filter(flight__flightnum__iexact=flightnum)
        if flightdate:
            tickets = tickets.filter(flight__flightdate=flightdate)
    else:
        tickets = tickets.none()
    return tickets.order_by("flight__flightdate", "flight__deptime", "ticketid")


def next_ticket_id() -> str:
    with connection.cursor() as cursor:
        cursor.execute("SELECT nextval('ticket_ticketid_seq')")
        number = cursor.fetchone()[0]
    return f"CB{number:08d}"


def reset_ticket_sequence() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COALESCE(MAX(CAST(SUBSTRING(ticketid FROM 3) AS BIGINT)), 0) + 1
            FROM ticket
            WHERE ticketid ~ '^CB[0-9]{8}$'
            """
        )
        next_number = cursor.fetchone()[0]
        cursor.execute("SELECT setval('ticket_ticketid_seq', %s, false)", [next_number])
