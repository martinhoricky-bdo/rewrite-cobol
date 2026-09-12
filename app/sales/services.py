"""Sales rules reconstruct SRCHTKT, SELLCOB1, missing SELLCOB2, PRINTCI, and PRINTPA use
cases.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal

from django.db import connection, transaction
from django.db.models import F, QuerySet, Value
from django.db.models.functions import Coalesce

from accounts.models import Employee
from core.messages import E_SEL_05, E_SEL_05_ID, E_SEL_06, E_SEL_07, E_SEL_08, E_SEL_10, E_SEL_11
from operations.models import Flight
from operations.services import free_seats_subquery

from .models import Buy, Passenger, Ticket

logger = logging.getLogger("cobol_airlines.sales")

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
    """Provide SaleError behavior for the sales legacy programs and UC-S01 through UC-S09."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class SaleQuote:
    """Provide SaleQuote behavior for the sales legacy programs and UC-S01 through UC-S09."""

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
        """Implement to_session behavior for the sales legacy programs and UC-S01 through
        UC-S09.
        """
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
        """Implement from_session behavior for the sales legacy programs and UC-S01 through
        UC-S09.
        """
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
    """Reconstruct SELLCOB1 (SELL1-COB), map SELLMS/SELLMP, for UC-S06.

    Checks E-SEL-01 through E-SEL-08 retain the ordering specified in functional section
    6.
    """
    # Preserve legacy validation order so callers receive the specified E-SEL message first.
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


def seat_layout(numseats: int) -> list[str]:
    """Implement seat_layout behavior for the sales legacy programs and UC-S01 through
    UC-S09.
    """
    return [f"{'ABCDEF'[index % 6]}{index // 6 + 1:02d}" for index in range(numseats)]


def assign_seats(flight: Flight, count: int) -> list[str]:
    """Implement assign_seats behavior for the sales legacy programs and UC-S01 through
    UC-S09.
    """
    occupied = set(flight.tickets.values_list("seat", flat=True))
    available = [seat for seat in seat_layout(flight.airplane.numseats) if seat not in occupied]
    if len(available) < count:
        raise SaleError("E_SEL_08", E_SEL_08.format(n=len(available)))
    return available[:count]


def resolve_passengers(client_ids: list[int], flight: Flight) -> list[Passenger]:
    """Implement resolve_passengers behavior for the sales legacy programs and UC-S01
    through UC-S09.
    """
    seen = set()
    for client_id in client_ids:
        if client_id in seen:
            raise SaleError("E_SEL_11", E_SEL_11.format(id=client_id))
        seen.add(client_id)

    passengers_by_id = Passenger.objects.in_bulk(client_ids)
    for client_id in client_ids:
        if client_id not in passengers_by_id:
            raise SaleError("E_SEL_05", E_SEL_05_ID.format(id=client_id))
        if flight.tickets.filter(client_id=client_id).exists():
            raise SaleError("E_SEL_10", E_SEL_10.format(id=client_id))
    return [passengers_by_id[client_id] for client_id in client_ids]


def confirm_sale(
    *, quote: SaleQuote, client_ids: list[int], seller: Employee, now: datetime
) -> Buy:
    """Reconstruct missing SELLCOB2 from SELL2-MAP and screenshots for UC-S07.

    Locks the flight with ``select_for_update`` before assigning seats and enforcing
    E-SEL-10 and E-SEL-11, preventing concurrent sales from allocating the same
    capacity.
    """
    if len(client_ids) != quote.count:
        raise ValueError("Passenger count does not match the sale quote.")
    with transaction.atomic():
        # Serialize capacity checks and seat assignment for concurrent sales of one flight.
        flight = (
            Flight.objects.select_for_update().select_related("airplane").get(pk=quote.flight_id)
        )
        passengers = resolve_passengers(client_ids, flight)
        seats = assign_seats(flight, quote.count)
        buy = Buy.objects.create(
            buydate=now.date(),
            buytime=now.time().replace(microsecond=0),
            price=quote.unit_price * quote.count,
            emp=seller,
            client=passengers[0],
        )
        tickets = [
            Ticket(
                ticketid=next_ticket_id(),
                buy=buy,
                client=passenger,
                flight=flight,
                seat=seat,
            )
            for passenger, seat in zip(passengers, seats, strict=True)
        ]
        Ticket.objects.bulk_create(tickets)
        logger.info(
            "sale buyid=%s user=%s flight=%s tickets=%s",
            buy.pk,
            seller.pk,
            flight.flightnum,
            len(tickets),
        )
        return buy


PASSENGER_EMAIL_WARNING = "Another passenger with this email already exists."


def duplicate_email_warning(email: str, exclude_pk: int | None = None) -> str | None:
    """Return the duplicate e-mail warning when another passenger uses the address."""
    duplicates = Passenger.objects.filter(email__iexact=email)
    if exclude_pk is not None:
        duplicates = duplicates.exclude(pk=exclude_pk)
    if duplicates.exists():
        return PASSENGER_EMAIL_WARNING
    return None


def legacy_date(d: date) -> str:
    """Format a date as PRINTCI and PRINTPA expect from the DB2-derived records."""
    return f"{d.day:02d}{LEGACY_MONTHS[d.month - 1]}{d.year:04d}"


def boarding_pass_context(ticket: Ticket) -> dict[str, str]:
    """Implement boarding_pass_context behavior for the sales legacy programs and UC-S01
    through UC-S09.
    """
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
    """Implement search_tickets behavior for the sales legacy programs and UC-S01 through
    UC-S09.
    """
    tickets = Ticket.objects.with_related()
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
    """Implement next_ticket_id behavior for the sales legacy programs and UC-S01 through
    UC-S09.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT nextval('ticket_ticketid_seq')")
        number = cursor.fetchone()[0]
    return f"CB{number:08d}"


def reset_ticket_sequence() -> None:
    """Implement reset_ticket_sequence behavior for the sales legacy programs and UC-S01
    through UC-S09.
    """
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
