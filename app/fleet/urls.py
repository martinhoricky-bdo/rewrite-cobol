from django.urls import path

from . import views

urlpatterns = [
    path("airports/", views.airports, name="airports"),
    path("airports/new/", views.airport_create, name="airport_create"),
    path("airports/<str:airportid>/edit/", views.airport_edit, name="airport_edit"),
    path("airports/<str:airportid>/delete/", views.airport_delete, name="airport_delete"),
    path("airplanes/", views.airplanes, name="airplanes"),
    path("airplanes/new/", views.airplane_create, name="airplane_create"),
    path("airplanes/<str:airplaneid>/edit/", views.airplane_edit, name="airplane_edit"),
    path("airplanes/<str:airplaneid>/delete/", views.airplane_delete, name="airplane_delete"),
]
