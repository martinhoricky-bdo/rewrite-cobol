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

from .forms import CrewForm, FlightForm, FlightGenerateForm, ShiftForm
from .models import Crew, Flight, Shift
from .services import generate_flights, schedule_crews, schedule_flights, schedule_shifts


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


@role_required(Role.SCHEDULE)
def crews(request):
    return render(request, "schedule/crew_list.html", {"crews": schedule_crews()})


def _crew_form(request, crew):
    form = CrewForm(request.POST or None, instance=crew)
    if request.method == "POST" and form.is_valid():
        saved = form.save()
        messages.success(request, f"Crew {saved.pk} saved.")
        return redirect("schedule:crews")
    return render(request, "schedule/crew_form.html", {"form": form, "object": crew})


@role_required(Role.SCHEDULE)
def crew_create(request):
    return _crew_form(request, Crew())


@role_required(Role.SCHEDULE)
def crew_edit(request, crewid):
    return _crew_form(request, get_object_or_404(Crew, pk=crewid))


@role_required(Role.SCHEDULE)
def crew_delete(request, crewid):
    crew = get_object_or_404(Crew, pk=crewid)
    if request.method == "POST":
        count = crew.shifts.count()
        if count:
            messages.error(request, E_REF_01.format(Entity="Crew", n=count, related="shifts"))
        else:
            crew.delete()
            messages.success(request, f"Crew {crewid} deleted.")
        return redirect("schedule:crews")
    return render(request, "schedule/crew_confirm_delete.html", {"crew": crew})


@role_required(Role.SCHEDULE)
def shifts(request):
    today = timezone.localdate()
    start, end = today, today + timedelta(days=30)
    try:
        if request.GET.get("date_from"):
            start = date.fromisoformat(request.GET["date_from"])
        if request.GET.get("date_to"):
            end = date.fromisoformat(request.GET["date_to"])
    except (TypeError, ValueError):
        pass
    try:
        crew_id = int(request.GET["crew"]) if request.GET.get("crew") else None
    except (TypeError, ValueError):
        crew_id = None
    page = Paginator(schedule_shifts(date_from=start, date_to=end, crew_id=crew_id), 20).get_page(
        request.GET.get("page")
    )
    params = request.GET.copy()
    params.pop("page", None)
    return render(
        request,
        "schedule/shift_list.html",
        {
            "page_obj": page,
            "date_from": start,
            "date_to": end,
            "selected_crew": crew_id,
            "crews": Crew.objects.order_by("crewid"),
            "query_params": params.urlencode(),
        },
    )


def _shift_form(request, shift):
    form = ShiftForm(request.POST or None, instance=shift)
    if request.method == "POST" and form.is_valid():
        saved = form.save()
        messages.success(request, f"Shift {saved.pk} saved.")
        return redirect("schedule:shifts")
    return render(request, "schedule/shift_form.html", {"form": form, "object": shift})


@role_required(Role.SCHEDULE)
def shift_create(request):
    return _shift_form(request, Shift())


@role_required(Role.SCHEDULE)
def shift_edit(request, shiftid):
    return _shift_form(request, get_object_or_404(Shift, pk=shiftid))


@role_required(Role.SCHEDULE)
def shift_delete(request, shiftid):
    shift = get_object_or_404(Shift, pk=shiftid)
    if request.method == "POST":
        count = shift.flights.count()
        if count:
            messages.error(request, E_REF_01.format(Entity="Shift", n=count, related="flights"))
        else:
            shift.delete()
            messages.success(request, f"Shift {shiftid} deleted.")
        return redirect("schedule:shifts")
    return render(request, "schedule/shift_confirm_delete.html", {"shift": shift})
