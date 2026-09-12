from django.urls import path

from . import views

urlpatterns = [
    path("airports/", views.AirportListView.as_view(), name="airports"),
    path("airports/new/", views.AirportCreateView.as_view(), name="airport_create"),
    path("airports/<str:airportid>/edit/", views.AirportUpdateView.as_view(), name="airport_edit"),
    path(
        "airports/<str:airportid>/delete/", views.AirportDeleteView.as_view(), name="airport_delete"
    ),
    path("airplanes/", views.AirplaneListView.as_view(), name="airplanes"),
    path("airplanes/new/", views.AirplaneCreateView.as_view(), name="airplane_create"),
    path(
        "airplanes/<str:airplaneid>/edit/", views.AirplaneUpdateView.as_view(), name="airplane_edit"
    ),
    path(
        "airplanes/<str:airplaneid>/delete/",
        views.AirplaneDeleteView.as_view(),
        name="airplane_delete",
    ),
]
