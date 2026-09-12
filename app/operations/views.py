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

from . import forms as f
from .models import Crew, Flight, Shift
from .services import generate_flights


class ScheduleView(RoleRequiredMixin):
    allowed_roles = (Role.SCHEDULE,)


class ScheduleFormView(
    ScheduleView, generic.PageTitleMixin, generic.CancelUrlMixin, generic.SavedMessageMixin
):
    template_name = "core/form.html"

    def get_page_title(self):
        if self.object:
            return f"Edit {self.model._meta.verbose_name} {self.object.pk}"
        return self.page_title


class ScheduleListView(ScheduleView, generic.PageTitleMixin, generic.FilteredListView):
    pass


class FlightView:
    model = Flight
    pk_url_kwarg = "flightid"
    success_url = reverse_lazy("schedule:flights")
    cancel_url_name = "schedule:flights"


class FlightListView(FlightView, ScheduleListView):
    page_title, template_name, filter_form_class, paginate_by = (
        "Flights",
        "schedule/flight_list.html",
        f.FlightFilterForm,
        10,
    )

    def filter_queryset(self, queryset, form):
        today = timezone.localdate()
        queryset = (
            queryset.in_period(
                form.value("date_from", today), form.value("date_to", today + timedelta(days=30))
            )
            .with_related()
            .select_related("shift__crew")
            .with_sold()
        )
        number, airport = form.value("flightnum", "").strip(), form.value("airport", "").strip()
        if number:
            queryset = queryset.filter(flightnum__iexact=number)
        if airport:
            queryset = queryset.filter(
                Q(airportdep__airportid__iexact=airport) | Q(airportarr__airportid__iexact=airport)
            )
        return queryset


class FlightCreateView(FlightView, ScheduleFormView, CreateView):
    form_class, page_title = f.FlightForm, "New flight"


class FlightUpdateView(FlightView, ScheduleFormView, UpdateView):
    form_class = f.FlightForm


class FlightDeleteView(FlightView, ScheduleView, generic.ProtectedDeleteView):
    page_title = "Delete flight"


class FlightGenerateView(ScheduleView, generic.PageTitleMixin, generic.CancelUrlMixin, FormView):
    form_class, template_name, page_title = (
        f.FlightGenerateForm,
        "schedule/flight_generate.html",
        "Generate flights",
    )
    cancel_url_name = "schedule:flights"

    def form_valid(self, form):
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
    model, pk_url_kwarg = Crew, "crewid"
    success_url, cancel_url_name = reverse_lazy("schedule:crews"), "schedule:crews"


class CrewListView(CrewView, ScheduleListView):
    page_title, template_name = "Crews", "schedule/crew_list.html"

    def filter_queryset(self, queryset, form):
        return queryset.with_members().with_shift_count()


class CrewCreateView(CrewView, ScheduleFormView, CreateView):
    form_class, page_title = f.CrewForm, "New crew"


class CrewUpdateView(CrewView, ScheduleFormView, UpdateView):
    form_class = f.CrewForm


class CrewDeleteView(CrewView, ScheduleView, generic.ProtectedDeleteView):
    page_title = "Delete crew"


class ShiftView:
    model, pk_url_kwarg = Shift, "shiftid"
    success_url, cancel_url_name = reverse_lazy("schedule:shifts"), "schedule:shifts"


class ShiftListView(ShiftView, ScheduleListView):
    page_title, template_name, filter_form_class, paginate_by = (
        "Shifts",
        "schedule/shift_list.html",
        f.ShiftFilterForm,
        20,
    )

    def filter_queryset(self, queryset, form):
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
    form_class, page_title = f.ShiftForm, "New shift"


class ShiftUpdateView(ShiftView, ScheduleFormView, UpdateView):
    form_class = f.ShiftForm


class ShiftDeleteView(ShiftView, ScheduleView, generic.ProtectedDeleteView):
    page_title = "Delete shift"
