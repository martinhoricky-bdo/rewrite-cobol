from django.urls import path

from . import views

app_name = "schedule"

urlpatterns = [
    path("crews/", views.crews, name="crews"),
    path("crews/new/", views.crew_create, name="crew_create"),
    path("crews/<int:crewid>/edit/", views.crew_edit, name="crew_edit"),
    path("crews/<int:crewid>/delete/", views.crew_delete, name="crew_delete"),
    path("shifts/", views.shifts, name="shifts"),
    path("shifts/new/", views.shift_create, name="shift_create"),
    path("shifts/<int:shiftid>/edit/", views.shift_edit, name="shift_edit"),
    path("shifts/<int:shiftid>/delete/", views.shift_delete, name="shift_delete"),
    path("flights/", views.flights, name="flights"),
    path("flights/new/", views.flight_create, name="flight_create"),
    path("flights/generate/", views.flights_generate, name="flights_generate"),
    path("flights/<int:flightid>/edit/", views.flight_edit, name="flight_edit"),
    path("flights/<int:flightid>/delete/", views.flight_delete, name="flight_delete"),
]
