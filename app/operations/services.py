from datetime import date

from django.db.models import Count, F, IntegerField, OuterRef, QuerySet, Subquery, Value
from django.db.models.functions import Coalesce

from sales.models import Ticket

from .models import Flight


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
