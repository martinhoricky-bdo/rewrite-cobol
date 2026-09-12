# fmt: off
# ruff: noqa: E501, I001
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from accounts.permissions import RoleRequiredMixin
from accounts.roles import Role
from core.views.generic import CancelUrlMixin, PageTitleMixin, ProtectedDeleteView, SavedMessageMixin

from .forms import AirplaneForm, AirportForm
from .models import Airplane, Airport

ROLES = (Role.IT, Role.SCHEDULE)

class FleetListView(RoleRequiredMixin, PageTitleMixin, ListView):
    allowed_roles = ROLES

class FleetFormView(RoleRequiredMixin, PageTitleMixin, CancelUrlMixin, SavedMessageMixin):
    allowed_roles, template_name = ROLES, "core/form.html"
    def get_page_title(self) -> str:
        return f"Edit {self.model._meta.verbose_name} {self.object.pk}" if self.object.pk else self.page_title

class FleetDeleteView(RoleRequiredMixin, ProtectedDeleteView):
    allowed_roles = ROLES

class AirportListView(FleetListView):
    model, context_object_name, page_title = Airport, "airports", "Airports"
class AirportCreateView(FleetFormView, CreateView):
    model, form_class, page_title, cancel_url_name = Airport, AirportForm, "New airport", "it:airports"
    success_url = reverse_lazy("it:airports")
class AirportUpdateView(FleetFormView, UpdateView):
    model, form_class, pk_url_kwarg, cancel_url_name = Airport, AirportForm, "airportid", "it:airports"
    success_url = reverse_lazy("it:airports")
class AirportDeleteView(FleetDeleteView):
    model, pk_url_kwarg, page_title = Airport, "airportid", "Delete airport"
    success_url = reverse_lazy("it:airports")
class AirplaneListView(FleetListView):
    model, context_object_name, page_title = Airplane, "airplanes", "Airplanes"
class AirplaneCreateView(FleetFormView, CreateView):
    model, form_class, page_title, cancel_url_name = Airplane, AirplaneForm, "New airplane", "it:airplanes"
    success_url = reverse_lazy("it:airplanes")
class AirplaneUpdateView(FleetFormView, UpdateView):
    model, form_class, pk_url_kwarg, cancel_url_name = Airplane, AirplaneForm, "airplaneid", "it:airplanes"
    success_url = reverse_lazy("it:airplanes")
class AirplaneDeleteView(FleetDeleteView):
    model, pk_url_kwarg, page_title = Airplane, "airplaneid", "Delete airplane"
    success_url = reverse_lazy("it:airplanes")
