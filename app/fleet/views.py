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
    """Serves the fleet form screen for Design catalogue maintenance in UC-I02 and UC-I03,
    applying the access, query, form, and redirect rules configured below.
    """

    allowed_roles = ROLES
    template_name = "core/form.html"

    def get_page_title(self) -> str:
        """Process get page title for Design catalogue maintenance in UC-I02 and UC-I03 according
        to the rules in this callable.
        """
        if not self.object:
            return self.page_title
        return f"Edit {self.model._meta.verbose_name} {self.object.pk}"


class FleetDeleteView(RoleRequiredMixin, generic.ProtectedDeleteView):
    """Serves the fleet delete screen for Design catalogue maintenance in UC-I02 and UC-I03,
    applying the access, query, form, and redirect rules configured below.
    """

    allowed_roles = ROLES


class AirportView:
    """Serves the airport screen for Design catalogue maintenance in UC-I02 and UC-I03,
    applying the access, query, form, and redirect rules configured below.
    """

    model = Airport
    pk_url_kwarg = "airportid"
    cancel_url_name = "it:airports"
    success_url = reverse_lazy("it:airports")


class AirplaneView:
    """Serves the airplane screen for Design catalogue maintenance in UC-I02 and UC-I03,
    applying the access, query, form, and redirect rules configured below.
    """

    model = Airplane
    pk_url_kwarg = "airplaneid"
    cancel_url_name = "it:airplanes"
    success_url = reverse_lazy("it:airplanes")


class AirportListView(AirportView, RoleRequiredMixin, generic.PageTitleMixin, ListView):
    """Serves the airport list screen for Design catalogue maintenance in UC-I02 and UC-I03,
    applying the access, query, form, and redirect rules configured below.
    """

    allowed_roles = ROLES
    page_title = "Airports"
    template_name = "it/airport_list.html"


class AirportCreateView(AirportView, FleetFormView, CreateView):
    """Serves the airport create screen for Design catalogue maintenance in UC-I02 and UC-I03,
    applying the access, query, form, and redirect rules configured below.
    """

    form_class = AirportForm
    page_title = "New airport"


class AirportUpdateView(AirportView, FleetFormView, UpdateView):
    """Serves the airport update screen for Design catalogue maintenance in UC-I02 and UC-I03,
    applying the access, query, form, and redirect rules configured below.
    """

    form_class = AirportForm


class AirportDeleteView(AirportView, FleetDeleteView):
    """Serves the airport delete screen for Design catalogue maintenance in UC-I02 and UC-I03,
    applying the access, query, form, and redirect rules configured below.
    """

    page_title = "Delete airport"


class AirplaneListView(AirplaneView, RoleRequiredMixin, generic.PageTitleMixin, ListView):
    """Serves the airplane list screen for Design catalogue maintenance in UC-I02 and UC-I03,
    applying the access, query, form, and redirect rules configured below.
    """

    allowed_roles = ROLES
    page_title = "Airplanes"
    template_name = "it/airplane_list.html"


class AirplaneCreateView(AirplaneView, FleetFormView, CreateView):
    """Serves the airplane create screen for Design catalogue maintenance in UC-I02 and UC-I03,
    applying the access, query, form, and redirect rules configured below.
    """

    form_class = AirplaneForm
    page_title = "New airplane"


class AirplaneUpdateView(AirplaneView, FleetFormView, UpdateView):
    """Serves the airplane update screen for Design catalogue maintenance in UC-I02 and UC-I03,
    applying the access, query, form, and redirect rules configured below.
    """

    form_class = AirplaneForm


class AirplaneDeleteView(AirplaneView, FleetDeleteView):
    """Serves the airplane delete screen for Design catalogue maintenance in UC-I02 and UC-I03,
    applying the access, query, form, and redirect rules configured below.
    """

    page_title = "Delete airplane"
