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
    allowed_roles = ROLES
    template_name = "core/form.html"

    def get_form_class(self):
        return AirportForm if self.model is Airport else AirplaneForm

    def get_page_title(self) -> str:
        if not self.object:
            return self.page_title
        return f"Edit {self.model._meta.verbose_name} {self.object.pk}"


class FleetDeleteView(RoleRequiredMixin, generic.ProtectedDeleteView):
    allowed_roles = ROLES


class AirportView:
    model = Airport
    pk_url_kwarg = "airportid"
    cancel_url_name = "it:airports"
    success_url = reverse_lazy("it:airports")


class AirplaneView:
    model = Airplane
    pk_url_kwarg = "airplaneid"
    cancel_url_name = "it:airplanes"
    success_url = reverse_lazy("it:airplanes")


class AirportListView(AirportView, RoleRequiredMixin, generic.PageTitleMixin, ListView):
    allowed_roles = ROLES
    page_title = "Airports"
    template_name = "it/airport_list.html"


class AirportCreateView(AirportView, FleetFormView, CreateView):
    page_title = "New airport"


class AirportUpdateView(AirportView, FleetFormView, UpdateView):
    pass


class AirportDeleteView(AirportView, FleetDeleteView):
    page_title = "Delete airport"


class AirplaneListView(AirplaneView, RoleRequiredMixin, generic.PageTitleMixin, ListView):
    allowed_roles = ROLES
    page_title = "Airplanes"
    template_name = "it/airplane_list.html"


class AirplaneCreateView(AirplaneView, FleetFormView, CreateView):
    page_title = "New airplane"


class AirplaneUpdateView(AirplaneView, FleetFormView, UpdateView):
    pass


class AirplaneDeleteView(AirplaneView, FleetDeleteView):
    page_title = "Delete airplane"
