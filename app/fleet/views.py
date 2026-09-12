"""Design: generic CRUD views for AIRPORT and AIRPLANE under UC-I02 and UC-I03, absent from
legacy screens.
"""

from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from accounts.permissions import RoleRequiredMixin
from accounts.roles import Role
from core.views import generic

from .forms import AirplaneForm, AirportForm
from .models import Airplane, Airport

ROLES = (Role.IT, Role.SCHEDULE)


class FleetFormView(
    RoleRequiredMixin, generic.PageTitleMixin, generic.CancelUrlMixin, generic.SavedMessageMixin
):
    """Shared base for the airport and airplane create and edit forms rendered by core/form.html."""

    allowed_roles = ROLES
    template_name = "core/form.html"

    def get_page_title(self) -> str:
        """Title the screen with the edited record, or with the create title."""
        if not self.object:
            return self.page_title
        return f"Edit {self.model._meta.verbose_name} {self.object.pk}"


class FleetDeleteView(RoleRequiredMixin, generic.ProtectedDeleteView):
    """Shared base for airport and airplane deletion, reporting E-REF-01 on a referenced record."""

    allowed_roles = ROLES


class AirportView:
    """Binds the AIRPORT table, the airportid lookup and the airport list redirects."""

    model = Airport
    pk_url_kwarg = "airportid"
    cancel_url_name = "it:airports"
    success_url = reverse_lazy("it:airports")


class AirplaneView:
    """Binds the AIRPLANE table, the airplaneid lookup and the airplane list redirects."""

    model = Airplane
    pk_url_kwarg = "airplaneid"
    cancel_url_name = "it:airplanes"
    success_url = reverse_lazy("it:airplanes")


class AirportListView(AirportView, RoleRequiredMixin, generic.PageTitleMixin, ListView):
    """Lists the whole AIRPORT catalogue for the IT and Schedule roles."""

    allowed_roles = ROLES
    page_title = "Airports"
    template_name = "it/airport_list.html"


class AirportCreateView(AirportView, FleetFormView, CreateView):
    """Creates an airport from AirportForm, which upper-cases the code and rejects duplicates."""

    form_class = AirportForm
    page_title = "New airport"


class AirportUpdateView(AirportView, FleetFormView, UpdateView):
    """Edits an existing airport; the airportid primary key stays unchanged."""

    form_class = AirportForm


class AirportDeleteView(AirportView, FleetDeleteView):
    """Deletes an airport unless flights still reference it, in which case E-REF-01 is shown."""

    page_title = "Delete airport"


class AirplaneListView(AirplaneView, RoleRequiredMixin, generic.PageTitleMixin, ListView):
    """Lists the AIRPLANE catalogue with seat counts for the IT and Schedule roles."""

    allowed_roles = ROLES
    page_title = "Airplanes"
    template_name = "it/airplane_list.html"


class AirplaneCreateView(AirplaneView, FleetFormView, CreateView):
    """Creates an airplane from AirplaneForm, which limits the seat count to the range 1-999."""

    form_class = AirplaneForm
    page_title = "New airplane"


class AirplaneUpdateView(AirplaneView, FleetFormView, UpdateView):
    """Edits an airplane; the seat count cannot drop below the tickets already sold."""

    form_class = AirplaneForm


class AirplaneDeleteView(AirplaneView, FleetDeleteView):
    """Deletes an airplane unless flights still reference it, in which case E-REF-01 is shown."""

    page_title = "Delete airplane"
