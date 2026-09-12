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
    """Provide ScheduleView behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT legacy
    lineage.
    """

    allowed_roles = (Role.SCHEDULE,)


class ScheduleFormView(
    ScheduleView, generic.PageTitleMixin, generic.CancelUrlMixin, generic.SavedMessageMixin
):
    """Provide ScheduleFormView behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT legacy
    lineage.
    """

    template_name = "core/form.html"

    def get_page_title(self):
        """Implement get_page_title behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT
        legacy lineage.
        """
        if self.object:
            return f"Edit {self.model._meta.verbose_name} {self.object.pk}"
        return self.page_title


class ScheduleListView(ScheduleView, generic.PageTitleMixin, generic.FilteredListView):
    """Provide ScheduleListView behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT legacy
    lineage.
    """

    pass


class FlightView:
    """Design: implement UC-P01 maintenance over the legacy FLIGHT data model."""

    model = Flight
    pk_url_kwarg = "flightid"
    success_url = reverse_lazy("schedule:flights")
    cancel_url_name = "schedule:flights"


class FlightListView(FlightView, ScheduleListView):
    """Design: implement UC-P01 maintenance over the legacy FLIGHT data model."""

    page_title = "Flights"
    template_name = "schedule/flight_list.html"
    filter_form_class = FlightFilterForm
    paginate_by = 10

    def filter_queryset(self, queryset, form):
        """Implement filter_queryset behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT
        legacy lineage.
        """
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
    """Design: implement UC-P01 maintenance over the legacy FLIGHT data model."""

    form_class = FlightForm
    page_title = "New flight"


class FlightUpdateView(FlightView, ScheduleFormView, UpdateView):
    """Design: implement UC-P01 maintenance over the legacy FLIGHT data model."""

    form_class = FlightForm


class FlightDeleteView(FlightView, ScheduleView, generic.ProtectedDeleteView):
    """Design: implement UC-P01 maintenance over the legacy FLIGHT data model."""

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
        """Implement form_valid behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT legacy
        lineage.
        """
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
    """Design: implement UC-P03 maintenance over the legacy CREW data model."""

    model = Crew
    pk_url_kwarg = "crewid"
    success_url = reverse_lazy("schedule:crews")
    cancel_url_name = "schedule:crews"


class CrewListView(CrewView, ScheduleListView):
    """Design: implement UC-P03 maintenance over the legacy CREW data model."""

    page_title = "Crews"
    template_name = "schedule/crew_list.html"

    def filter_queryset(self, queryset, form):
        """Implement filter_queryset behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT
        legacy lineage.
        """
        return queryset.with_members().with_shift_count()


class CrewCreateView(CrewView, ScheduleFormView, CreateView):
    """Design: implement UC-P03 maintenance over the legacy CREW data model."""

    form_class = CrewForm
    page_title = "New crew"


class CrewUpdateView(CrewView, ScheduleFormView, UpdateView):
    """Design: implement UC-P03 maintenance over the legacy CREW data model."""

    form_class = CrewForm


class CrewDeleteView(CrewView, ScheduleView, generic.ProtectedDeleteView):
    """Design: implement UC-P03 maintenance over the legacy CREW data model."""

    page_title = "Delete crew"


class ShiftView:
    """Design: implement UC-P04 maintenance over the legacy SHIFT data model."""

    model = Shift
    pk_url_kwarg = "shiftid"
    success_url = reverse_lazy("schedule:shifts")
    cancel_url_name = "schedule:shifts"


class ShiftListView(ShiftView, ScheduleListView):
    """Design: implement UC-P04 maintenance over the legacy SHIFT data model."""

    page_title = "Shifts"
    template_name = "schedule/shift_list.html"
    filter_form_class = ShiftFilterForm
    paginate_by = 20

    def filter_queryset(self, queryset, form):
        """Implement filter_queryset behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT
        legacy lineage.
        """
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
    """Design: implement UC-P04 maintenance over the legacy SHIFT data model."""

    form_class = ShiftForm
    page_title = "New shift"


class ShiftUpdateView(ShiftView, ScheduleFormView, UpdateView):
    """Design: implement UC-P04 maintenance over the legacy SHIFT data model."""

    form_class = ShiftForm


class ShiftDeleteView(ShiftView, ScheduleView, generic.ProtectedDeleteView):
    """Design: implement UC-P04 maintenance over the legacy SHIFT data model."""

    page_title = "Delete shift"
