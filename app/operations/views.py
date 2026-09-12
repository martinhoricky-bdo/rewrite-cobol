"""Design: schedule views implement UC-P01, UC-P03, and UC-P04; generation reconstructs
CBFLIGHT for UC-P02.
"""

from datetime import timedelta
from urllib.parse import urlencode

from django.contrib import messages
from django.db.models import Q
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, FormView, UpdateView

from accounts.permissions import RoleRequiredMixin
from accounts.roles import Role
from core.views import generic

from .forms import (
    CrewForm,
    FlightFilterForm,
    FlightForm,
    FlightGenerateForm,
    ShiftFilterForm,
    ShiftForm,
)
from .models import Crew, Flight, Shift
from .services import generate_flights


class ScheduleView(RoleRequiredMixin):
    """Restricts every schedule screen to the Schedule role."""

    allowed_roles = (Role.SCHEDULE,)


class ScheduleFormView(
    ScheduleView, generic.PageTitleMixin, generic.CancelUrlMixin, generic.SavedMessageMixin
):
    """Shared base for the flight, crew and shift forms rendered by core/form.html."""

    template_name = "core/form.html"

    def get_page_title(self):
        """Title the screen with the edited record, or with the create title."""
        if self.object:
            return f"Edit {self.model._meta.verbose_name} {self.object.pk}"
        return self.page_title


class ScheduleListView(ScheduleView, generic.PageTitleMixin, generic.FilteredListView):
    """Shared base for the filtered flight, crew and shift lists."""

    pass


class FlightView:
    """Restricts flight maintenance screens for Design UC-P01 over the legacy FLIGHT data model."""

    model = Flight
    pk_url_kwarg = "flightid"
    success_url = reverse_lazy("schedule:flights")
    cancel_url_name = "schedule:flights"


class FlightListView(FlightView, ScheduleListView):
    """Lists and filters flights with the counts required by Design UC-P01."""

    page_title = "Flights"
    template_name = "schedule/flight_list.html"
    filter_form_class = FlightFilterForm
    paginate_by = 10

    def filter_queryset(self, queryset, form):
        """Filter flights by period, number and airports and count the tickets sold."""
        today = timezone.localdate()
        queryset = (
            queryset.in_period(
                form.value("date_from", today), form.value("date_to", today + timedelta(days=30))
            )
            .with_related()
            .select_related("shift__crew")
            .with_sold()
            .order_by("flightdate", "deptime", "flightnum")
        )
        number = form.value("flightnum", "").strip()
        airport = form.value("airport", "").strip()
        if number:
            queryset = queryset.filter(flightnum__iexact=number)
        if airport:
            queryset = queryset.filter(
                Q(airportdep__airportid__iexact=airport) | Q(airportarr__airportid__iexact=airport)
            )
        return queryset


class FlightCreateView(FlightView, ScheduleFormView, CreateView):
    """Creates a flight record through the validated Design UC-P01 maintenance form."""

    form_class = FlightForm
    page_title = "New flight"


class FlightUpdateView(FlightView, ScheduleFormView, UpdateView):
    """Updates a flight record through the validated Design UC-P01 maintenance form."""

    form_class = FlightForm


class FlightDeleteView(FlightView, ScheduleView, generic.ProtectedDeleteView):
    """Deletes a flight record for Design UC-P01, subject to protected relationship constraints."""

    page_title = "Delete flight"


class FlightGenerateView(ScheduleView, generic.PageTitleMixin, generic.CancelUrlMixin, FormView):
    """Reconstruct CBFLIGHT (COB-PROG/FLIGHT-DUPLICATE/FLIGHT-DUPLICATE-COB) generation for
    UC-P02.
    """

    form_class = FlightGenerateForm
    template_name = "schedule/flight_generate.html"
    page_title = "Generate flights"
    cancel_url_name = "schedule:flights"

    def form_valid(self, form):
        """Generate the flights, report created and skipped counts, return to the list."""
        result = generate_flights(
            form.cleaned_data["template"],
            form.cleaned_data["date_from"],
            form.cleaned_data["date_to"],
            form.selected_weekdays(),
        )
        messages.success(
            self.request, f"Generated {result.created} flights, skipped {result.skipped} existing."
        )
        query = urlencode(
            {"date_from": form.cleaned_data["date_from"], "date_to": form.cleaned_data["date_to"]}
        )
        self.success_url = f"{reverse('schedule:flights')}?{query}"
        return super().form_valid(form)


class CrewView:
    """Restricts crew maintenance screens for Design UC-P03 over the legacy CREW data model."""

    model = Crew
    pk_url_kwarg = "crewid"
    success_url = reverse_lazy("schedule:crews")
    cancel_url_name = "schedule:crews"


class CrewListView(CrewView, ScheduleListView):
    """Lists and filters crews with the relations required by Design UC-P03."""

    page_title = "Crews"
    template_name = "schedule/crew_list.html"

    def filter_queryset(self, queryset, form):
        """Join the crew members and count their shifts."""
        return queryset.with_members().with_shift_count()


class CrewCreateView(CrewView, ScheduleFormView, CreateView):
    """Creates a crew record through the validated Design UC-P03 maintenance form."""

    form_class = CrewForm
    page_title = "New crew"


class CrewUpdateView(CrewView, ScheduleFormView, UpdateView):
    """Updates a crew record through the validated Design UC-P03 maintenance form."""

    form_class = CrewForm


class CrewDeleteView(CrewView, ScheduleView, generic.ProtectedDeleteView):
    """Deletes a crew record for Design UC-P03, subject to protected relationship constraints."""

    page_title = "Delete crew"


class ShiftView:
    """Restricts shift maintenance screens for Design UC-P04 over the legacy SHIFT data model."""

    model = Shift
    pk_url_kwarg = "shiftid"
    success_url = reverse_lazy("schedule:shifts")
    cancel_url_name = "schedule:shifts"


class ShiftListView(ShiftView, ScheduleListView):
    """Lists and filters shifts with the counts required by Design UC-P04."""

    page_title = "Shifts"
    template_name = "schedule/shift_list.html"
    filter_form_class = ShiftFilterForm
    paginate_by = 20

    def filter_queryset(self, queryset, form):
        """Filter shifts by period and crew and count their flights."""
        today = timezone.localdate()
        return (
            queryset.in_period(
                form.value("date_from", today), form.value("date_to", today + timedelta(days=30))
            )
            .for_crew(getattr(form.value("crew"), "pk", None))
            .select_related("crew")
            .with_flight_count()
            .order_by("shiftdate", "begintime", "shiftid")
        )


class ShiftCreateView(ShiftView, ScheduleFormView, CreateView):
    """Creates a shift record through the validated Design UC-P04 maintenance form."""

    form_class = ShiftForm
    page_title = "New shift"


class ShiftUpdateView(ShiftView, ScheduleFormView, UpdateView):
    """Updates a shift record through the validated Design UC-P04 maintenance form."""

    form_class = ShiftForm


class ShiftDeleteView(ShiftView, ScheduleView, generic.ProtectedDeleteView):
    """Deletes a shift record for Design UC-P04, subject to protected relationship constraints."""

    page_title = "Delete shift"
