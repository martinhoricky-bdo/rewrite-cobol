from django.urls import path

from . import views

app_name = "schedule"
urlpatterns = [
    path("crews/", views.CrewListView.as_view(), name="crews"),
    path("crews/new/", views.CrewCreateView.as_view(), name="crew_create"),
    path("crews/<int:crewid>/edit/", views.CrewUpdateView.as_view(), name="crew_edit"),
    path("crews/<int:crewid>/delete/", views.CrewDeleteView.as_view(), name="crew_delete"),
    path("shifts/", views.ShiftListView.as_view(), name="shifts"),
    path("shifts/new/", views.ShiftCreateView.as_view(), name="shift_create"),
    path("shifts/<int:shiftid>/edit/", views.ShiftUpdateView.as_view(), name="shift_edit"),
    path("shifts/<int:shiftid>/delete/", views.ShiftDeleteView.as_view(), name="shift_delete"),
    path("flights/", views.FlightListView.as_view(), name="flights"),
    path("flights/new/", views.FlightCreateView.as_view(), name="flight_create"),
    path("flights/generate/", views.FlightGenerateView.as_view(), name="flights_generate"),
    path("flights/<int:flightid>/edit/", views.FlightUpdateView.as_view(), name="flight_edit"),
    path("flights/<int:flightid>/delete/", views.FlightDeleteView.as_view(), name="flight_delete"),
]
