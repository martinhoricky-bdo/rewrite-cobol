from django.urls import path

from . import views

app_name = "sales"

urlpatterns = [
    path("flights/", views.flight_search, name="flight_search"),
    path("tickets/", views.ticket_search, name="ticket_search"),
    path("tickets/<str:ticketid>/", views.ticket_detail, name="ticket_detail"),
]
