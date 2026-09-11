from datetime import date

from django.db import connection
from django.db.models import QuerySet

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
