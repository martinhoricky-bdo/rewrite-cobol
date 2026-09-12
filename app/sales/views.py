import re
from decimal import DecimalException

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.html import format_html

from accounts.permissions import role_required
from accounts.roles import Role
from core.messages import E_FLT_03, E_SEL_05_ID, E_SEL_09, E_TKT_02, E_TKT_03
from operations.services import search_flights

from .forms import (
    FlightSearchForm,
    PassengerFilterForm,
    PassengerForm,
    SellStep1Form,
    SellStep2Form,
    TicketSearchForm,
)
from .models import Buy, Passenger, Ticket
from .services import (
    SESSION_KEY,
    SaleError,
    SaleQuote,
    boarding_pass_context,
    confirm_sale,
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
    quote = _session_quote(request)
    if quote is None:
        messages.error(request, E_SEL_09)
        return redirect("sales:sell_step1")

    if request.method == "POST" and request.POST.get("action") == "return":
        return redirect("sales:sell_step1")

    initial = {"client_1": quote.client_id}
    form = SellStep2Form(
        quote.count,
        data=request.POST if request.method == "POST" else None,
        initial=initial,
    )
    names = {1: quote.client_name} if request.method == "GET" else {}
    if request.method == "POST" and form.is_valid():
        client_ids = [form.cleaned_data[f"client_{number}"] for number in range(1, quote.count + 1)]
        if request.POST.get("action") == "confirm":
            try:
                buy = confirm_sale(
                    quote=quote,
                    client_ids=client_ids,
                    seller=request.user.employee,
                    now=timezone.localtime(),
                )
            except SaleError as exc:
                messages.error(request, exc.message)
            else:
                request.session.pop(SESSION_KEY, None)
                return redirect("sales:buy_detail", buyid=buy.pk)
        for number, client_id in enumerate(client_ids, start=1):
            passenger = Passenger.objects.filter(pk=client_id).first()
            names[number] = passenger.full_name if passenger else E_SEL_05_ID.format(id=client_id)

    rows = [
        {"field": form[f"client_{number}"], "name": names.get(number, "")}
        for number in range(1, quote.count + 1)
    ]
    return render(
        request,
        "sales/sell_step2.html",
        {"quote": quote, "form": form, "rows": rows},
    )


@role_required(Role.SALES)
def passenger_name(request):
    raw_client_id = request.GET.get("clientid")
    if raw_client_id is None:
        raw_client_id = next(
            (value for key, value in request.GET.items() if key.startswith("client_")), ""
        )
    try:
        client_id = int(raw_client_id)
    except ValueError:
        client_id = 0
    passenger = Passenger.objects.filter(pk=client_id).first()
    if passenger:
        return HttpResponse(format_html('<span class="name">{}</span>', passenger.full_name))
    return HttpResponse(
        format_html('<span class="error">{}</span>', E_SEL_05_ID.format(id=client_id))
    )


@role_required(Role.SALES, Role.CEO)
def buy_detail(request, buyid):
    buy = get_object_or_404(
        Buy.objects.select_related("emp", "client").prefetch_related("tickets__client"),
        pk=buyid,
    )
    return render(request, "sales/buy_detail.html", {"buy": buy})


@role_required(Role.SALES, Role.CEO)
def receipt(request, buyid):
    buy = get_object_or_404(Buy, pk=buyid)
    return render(request, "sales/receipt.html", {"buy": buy})


@role_required(Role.SALES, Role.CEO)
def boarding_passes(request, buyid):
    buy = get_object_or_404(Buy, pk=buyid)
    tickets = buy.tickets.select_related(
        "client", "flight", "flight__airportdep", "flight__airportarr"
    ).order_by("ticketid")
    passes = [boarding_pass_context(ticket) for ticket in tickets]
    return render(
        request,
        "sales/boarding_passes.html",
        {"buy": buy, "boarding_passes": passes},
    )


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
    return render(
        request,
        "sales/boarding_pass.html",
        {"boarding_pass": boarding_pass_context(ticket), "ticketid": ticket.ticketid},
    )
