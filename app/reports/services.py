from datetime import date
from decimal import Decimal

from django.db.models import (
    Avg,
    Count,
    DecimalField,
    ExpressionWrapper,
    F,
    IntegerField,
    OuterRef,
    Prefetch,
    Q,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce

from operations.models import Flight, Shift
from sales.models import Buy, Ticket


def crew_shifts(employee, *, today: date, include_past: bool = False):
    """Return shifts assigned to an employee, including flight passenger counts."""
    start = today if not include_past else date.fromordinal(today.toordinal() - 90)
    membership = (
        Q(crew__commander=employee)
        | Q(crew__copilote=employee)
        | Q(crew__fachief=employee)
        | Q(crew__fliattendant1=employee)
        | Q(crew__fliattendant2=employee)
        | Q(crew__fliattendant3=employee)
    )
    flights = Flight.objects.select_related("airportdep", "airportarr", "airplane").annotate(
        passenger_count=Count("tickets")
    )
    return (
        Shift.objects.filter(membership, shiftdate__gte=start)
        .select_related("crew")
        .prefetch_related(Prefetch("flights", queryset=flights))
        .order_by("shiftdate", "begintime", "shiftid")
        .distinct()
    )


def dashboard_report(date_from: date, date_to: date) -> dict:
    """Build all CEO dashboard figures with database-side aggregation."""
    buys = Buy.objects.filter(buydate__range=(date_from, date_to))
    flights = Flight.objects.filter(flightdate__range=(date_from, date_to))
    money = DecimalField(max_digits=12, decimal_places=2)
    buy_totals = buys.aggregate(
        sales=Count("pk"),
        revenue=Coalesce(Sum("price"), Value(Decimal("0.00")), output_field=money),
    )
    ticket_total = Ticket.objects.filter(buy__buydate__range=(date_from, date_to)).count()

    top_routes = (
        flights.values("airportdep_id", "airportarr_id")
        .annotate(ticket_count=Count("tickets"))
        .order_by("-ticket_count", "airportdep_id", "airportarr_id")[:5]
    )
    sales_by_seller = (
        buys.values("emp_id", "emp__firstname", "emp__lastname")
        .annotate(
            sale_count=Count("pk"),
            revenue=Coalesce(Sum("price"), Value(Decimal("0.00")), output_field=money),
        )
        .order_by("-revenue", "emp_id")
    )
    sold_for_flight = (
        Ticket.objects.filter(flight_id=OuterRef("pk"))
        .values("flight_id")
        .annotate(total=Count("pk"))
        .values("total")
    )
    flights_with_load = flights.annotate(
        sold_for_flight=Coalesce(Subquery(sold_for_flight, output_field=IntegerField()), 0)
    )
    load_expression = ExpressionWrapper(
        Value(Decimal("100.0")) * F("sold_for_flight") / F("airplane__numseats"),
        output_field=DecimalField(max_digits=7, decimal_places=2),
    )
    flight_totals = flights_with_load.aggregate(
        flights=Count("pk"), average_load_factor=Coalesce(Avg(load_expression), Decimal("0.00"))
    )
    load_by_flight_number = (
        flights_with_load.values("flightnum")
        .annotate(
            load_factor=Avg(load_expression),
        )
        .order_by("flightnum")
    )
    return {
        **buy_totals,
        "tickets": ticket_total,
        **flight_totals,
        "top_routes": top_routes,
        "sales_by_seller": sales_by_seller,
        "load_by_flight_number": load_by_flight_number,
    }
