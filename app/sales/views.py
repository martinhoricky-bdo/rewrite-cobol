import re

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils import timezone

from accounts.permissions import role_required
from accounts.roles import Role
from core.messages import E_FLT_03, E_TKT_02, E_TKT_03
from operations.services import search_flights

from .forms import FlightSearchForm, TicketSearchForm
from .models import Ticket
from .services import search_tickets


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
