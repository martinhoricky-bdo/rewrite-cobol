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
    allowed_roles = (Role.SCHEDULE,)


class ModelView:
    pk_url_kwarg = "pk"
    template_name = "core/form.html"

    def get_page_title(self):
        return (
            self.page_title
            if not self.object
            else f"Edit {self.model._meta.verbose_name} {self.object.pk}"
        )


class FlightView(ModelView):
    model = Flight
    pk_url_kwarg = "flightid"
    success_url = reverse_lazy("schedule:flights")
    cancel_url_name = "schedule:flights"


class FlightListView(FlightView, ScheduleView, generic.PageTitleMixin, generic.FilteredListView):
    page_title = "Flights"
    template_name = "schedule/flight_list.html"
    filter_form_class = FlightFilterForm
    paginate_by = 10

    def filter_queryset(self, queryset, form):
        today = timezone.localdate()
        start = form.value("date_from", today)
        end = form.value("date_to", today + timedelta(days=30))
        queryset = (
            queryset.in_period(start, end).with_related().select_related("shift__crew").with_sold()
        )
        number, airport = form.value("flightnum", "").strip(), form.value("airport", "").strip()
        if number:
            queryset = queryset.filter(flightnum__iexact=number)
        if airport:
            queryset = queryset.filter(
                Q(airportdep_id__iexact=airport) | Q(airportarr_id__iexact=airport)
            )
        return queryset


class FlightFormView(
    FlightView,
    ScheduleView,
    generic.PageTitleMixin,
    generic.CancelUrlMixin,
    generic.SavedMessageMixin,
):
    pass


class FlightCreateView(FlightFormView, CreateView):
    form_class = FlightForm
    page_title = "New flight"


class FlightUpdateView(FlightFormView, UpdateView):
    form_class = FlightForm


class FlightDeleteView(FlightView, ScheduleView, generic.ProtectedDeleteView):
    page_title = "Delete flight"


class FlightGenerateView(ScheduleView, generic.PageTitleMixin, generic.CancelUrlMixin, FormView):
    form_class = FlightGenerateForm
    template_name = "schedule/flight_generate.html"
    page_title = "Generate flights"
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


class CrewView(ModelView):
    model = Crew
    pk_url_kwarg = "crewid"
    success_url = reverse_lazy("schedule:crews")
    cancel_url_name = "schedule:crews"


class CrewListView(CrewView, ScheduleView, generic.PageTitleMixin, generic.FilteredListView):
    page_title = "Crews"
    template_name = "schedule/crew_list.html"

    def get_queryset(self):
        return Crew.objects.with_members().with_shift_count()


class CrewFormView(
    CrewView,
    ScheduleView,
    generic.PageTitleMixin,
    generic.CancelUrlMixin,
    generic.SavedMessageMixin,
):
    pass


class CrewCreateView(CrewFormView, CreateView):
    form_class = CrewForm
    page_title = "New crew"


class CrewUpdateView(CrewFormView, UpdateView):
    form_class = CrewForm


class CrewDeleteView(CrewView, ScheduleView, generic.ProtectedDeleteView):
    page_title = "Delete crew"


class ShiftView(ModelView):
    model = Shift
    pk_url_kwarg = "shiftid"
    success_url = reverse_lazy("schedule:shifts")
    cancel_url_name = "schedule:shifts"


class ShiftListView(ShiftView, ScheduleView, generic.PageTitleMixin, generic.FilteredListView):
    page_title = "Shifts"
    template_name = "schedule/shift_list.html"
    filter_form_class = ShiftFilterForm
    paginate_by = 20

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


class ShiftFormView(
    ShiftView,
    ScheduleView,
    generic.PageTitleMixin,
    generic.CancelUrlMixin,
    generic.SavedMessageMixin,
):
    pass


class ShiftCreateView(ShiftFormView, CreateView):
    form_class = ShiftForm
    page_title = "New shift"


class ShiftUpdateView(ShiftFormView, UpdateView):
    form_class = ShiftForm


class ShiftDeleteView(ShiftView, ScheduleView, generic.ProtectedDeleteView):
    page_title = "Delete shift"
