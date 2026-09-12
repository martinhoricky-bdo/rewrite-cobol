from django.urls import path

from . import views

app_name = "schedule"

urlpatterns = [
    path("flights/", views.flights, name="flights"),
    path("flights/new/", views.flight_create, name="flight_create"),
    path("flights/generate/", views.flights_generate, name="flights_generate"),
    path("flights/<int:flightid>/edit/", views.flight_edit, name="flight_edit"),
    path("flights/<int:flightid>/delete/", views.flight_delete, name="flight_delete"),
]
