from datetime import date, timedelta

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.permissions import role_required
from accounts.roles import Role
from core.messages import E_REF_01

from .forms import FlightForm, FlightGenerateForm
from .models import Flight
from .services import generate_flights, schedule_flights


@role_required(Role.SCHEDULE)
def flights(request):
    today = timezone.localdate()
    start, end = today, today + timedelta(days=30)
    try:
        if request.GET.get("date_from"):
            start = date.fromisoformat(request.GET["date_from"])
        if request.GET.get("date_to"):
            end = date.fromisoformat(request.GET["date_to"])
    except (TypeError, ValueError):
        pass
    queryset = schedule_flights(
        date_from=start,
        date_to=end,
        flightnum=request.GET.get("flightnum", ""),
        airport=request.GET.get("airport", ""),
    )
    page = Paginator(queryset, 10).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(
        request,
        "schedule/flight_list.html",
        {
            "page_obj": page,
            "date_from": start,
            "date_to": end,
            "query_params": params.urlencode(),
        },
    )


def _flight_form(request, flight):
    form = FlightForm(request.POST or None, instance=flight)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            saved = form.save()
        messages.success(request, f"Flight {saved.pk} saved.")
        return redirect("schedule:flights")
    return render(request, "schedule/flight_form.html", {"form": form, "object": flight})


@role_required(Role.SCHEDULE)
def flight_create(request):
    return _flight_form(request, Flight())


@role_required(Role.SCHEDULE)
def flight_edit(request, flightid):
    return _flight_form(request, get_object_or_404(Flight, pk=flightid))


@role_required(Role.SCHEDULE)
def flight_delete(request, flightid):
    flight = get_object_or_404(Flight, pk=flightid)
    if request.method == "POST":
        count = flight.tickets.count()
        if count:
            messages.error(request, E_REF_01.format(Entity="Flight", n=count, related="tickets"))
        else:
            with transaction.atomic():
                flight.delete()
            messages.success(request, f"Flight {flightid} deleted.")
        return redirect("schedule:flights")
    return render(request, "schedule/flight_confirm_delete.html", {"flight": flight})


@role_required(Role.SCHEDULE)
def flights_generate(request):
    form = FlightGenerateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        result = generate_flights(
            form.cleaned_data["template"],
            form.cleaned_data["date_from"],
            form.cleaned_data["date_to"],
            form.selected_weekdays(),
        )
        messages.success(
            request, f"Generated {result.created} flights, skipped {result.skipped} existing."
        )
        query = (
            f"date_from={form.cleaned_data['date_from'].isoformat()}&"
            f"date_to={form.cleaned_data['date_to'].isoformat()}"
        )
        return redirect(f"{reverse('schedule:flights')}?{query}")
    return render(request, "schedule/flight_generate.html", {"form": form})
