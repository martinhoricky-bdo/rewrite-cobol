import re
from decimal import DecimalException

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.permissions import role_required
from accounts.roles import Role
from core.messages import E_FLT_03, E_SEL_09, E_TKT_02, E_TKT_03
from operations.services import search_flights

from .forms import (
    FlightSearchForm,
    PassengerFilterForm,
    PassengerForm,
    SellStep1Form,
    TicketSearchForm,
)
from .models import Passenger, Ticket
from .services import (
    SESSION_KEY,
    SaleError,
    SaleQuote,
    boarding_pass_context,
    filter_passengers,
    quote_sale,
    search_tickets,
)

PASSENGER_EMAIL_WARNING = "Another passenger with this email already exists."


def _session_quote(request):
    data = request.session.get(SESSION_KEY)
    if data is None:
        return None
    try:
        return SaleQuote.from_session(data)
    except (DecimalException, KeyError, TypeError, ValueError):
        request.session.pop(SESSION_KEY, None)
        return None


@role_required(Role.SALES)
def sell_step1(request):
    quote = _session_quote(request)
    if request.method == "POST":
        form = SellStep1Form(request.POST)
        if form.is_valid():
            try:
                quote = quote_sale(**form.cleaned_data, today=timezone.localdate())
            except SaleError as exc:
                request.session.pop(SESSION_KEY, None)
                quote = None
                messages.error(request, exc.message)
            else:
                request.session[SESSION_KEY] = quote.to_session()
        else:
            request.session.pop(SESSION_KEY, None)
            quote = None
            for errors in form.errors.values():
                for error in errors:
                    messages.error(request, error)
    else:
        form = SellStep1Form(
            initial={
                "clientid": request.GET.get("clientid", ""),
                "flightnum": request.GET.get("flightnum", ""),
                "flightdate": request.GET.get("date", ""),
            }
        )
    return render(request, "sales/sell_step1.html", {"form": form, "quote": quote})


@role_required(Role.SALES)
def sell_step2(request):
    if _session_quote(request) is None:
        messages.error(request, E_SEL_09)
        return redirect("sales:sell_step1")
    return render(request, "sales/sell_step2_placeholder.html")


@role_required(Role.SALES)
def passenger_list(request):
    form = PassengerFilterForm(request.GET)
    passengers = Passenger.objects.none()
    if form.is_valid():
        passengers = filter_passengers(**form.cleaned_data)
    paginator = Paginator(passengers, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    query_params = request.GET.copy()
    query_params.pop("page", None)
    return render(
        request,
        "sales/passenger_list.html",
        {"form": form, "page_obj": page_obj, "query_params": query_params.urlencode()},
    )


@role_required(Role.SALES)
def passenger_detail(request, clientid):
    passenger = get_object_or_404(Passenger, clientid=clientid)
    tickets = passenger.tickets.select_related(
        "flight", "flight__airportdep", "flight__airportarr"
    ).order_by("flight__flightdate", "flight__deptime", "ticketid")
    return render(
        request,
        "sales/passenger_detail.html",
        {"passenger": passenger, "tickets": tickets},
    )


def _save_passenger(request, *, passenger=None):
    form = PassengerForm(request.POST or None, instance=passenger)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        duplicates = Passenger.objects.filter(email__iexact=email)
        if passenger is not None:
            duplicates = duplicates.exclude(clientid=passenger.clientid)
        if duplicates.exists():
            messages.warning(request, PASSENGER_EMAIL_WARNING)
        saved = form.save()
        messages.success(request, f"Passenger {saved.clientid} saved.")
        return redirect("sales:passenger_detail", clientid=saved.clientid)
    return render(
        request,
        "sales/passenger_form.html",
        {"form": form, "passenger": passenger},
    )


@role_required(Role.SALES)
def passenger_create(request):
    return _save_passenger(request)


@role_required(Role.SALES)
def passenger_edit(request, clientid):
    passenger = get_object_or_404(Passenger, clientid=clientid)
    return _save_passenger(request, passenger=passenger)


@role_required(Role.SALES, Role.CEO, Role.SCHEDULE, Role.CREW)
def flight_search(request):
    form = FlightSearchForm(request.GET or None)
    page_obj = None
    if form.is_bound:
        if form.is_valid():
            flights = search_flights(**form.cleaned_data, today=timezone.localdate())
            paginator = Paginator(flights, 10)
            page_obj = paginator.get_page(request.GET.get("page"))
            if paginator.count == 0:
                messages.info(request, E_FLT_03)
        else:
            for errors in form.errors.values():
                for error in errors:
                    messages.error(request, error)

    query_params = request.GET.copy()
    query_params.pop("page", None)
    return render(
        request,
        "sales/flight_search.html",
        {"form": form, "page_obj": page_obj, "query_params": query_params.urlencode()},
    )


@role_required(Role.SALES, Role.CEO)
def ticket_search(request):
    form = TicketSearchForm(request.GET or None)
    page_obj = None
    if form.is_bound:
        if form.is_valid():
            ticketid = form.cleaned_data.get("ticketid")
            if ticketid and not re.fullmatch(r"CB\d{8}", ticketid, re.IGNORECASE):
                tickets = Ticket.objects.none()
            else:
                tickets = search_tickets(**form.cleaned_data)
            paginator = Paginator(tickets, 10)
            page_obj = paginator.get_page(request.GET.get("page"))
            if paginator.count == 0:
                messages.info(request, E_TKT_02)
        else:
            for errors in form.errors.values():
                for error in errors:
                    messages.error(request, error)
    query_params = request.GET.copy()
    query_params.pop("page", None)
    return render(
        request,
        "sales/ticket_search.html",
        {"form": form, "page_obj": page_obj, "query_params": query_params.urlencode()},
    )


@role_required(Role.SALES, Role.CEO)
def ticket_detail(request, ticketid):
    ticket = (
        Ticket.objects.select_related(
            "client", "flight", "flight__airportdep", "flight__airportarr", "buy", "buy__emp"
        )
        .filter(ticketid=ticketid.upper())
        .first()
    )
    if ticket is None:
        return render(request, "404.html", {"error_message": E_TKT_03}, status=404)
    return render(request, "sales/ticket_detail.html", {"ticket": ticket})


@role_required(Role.SALES, Role.CEO)
def boarding_pass(request, ticketid):
    ticket = (
        Ticket.objects.select_related(
            "client", "flight", "flight__airportdep", "flight__airportarr"
        )
        .filter(ticketid=ticketid.upper())
        .first()
    )
    if ticket is None:
        return render(request, "404.html", {"error_message": E_TKT_03}, status=404)
    return render(request, "sales/boarding_pass.html", boarding_pass_context(ticket))
