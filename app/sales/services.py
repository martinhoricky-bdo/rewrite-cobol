from datetime import date

from django.db import connection
from django.db.models import QuerySet

from .models import Ticket


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
