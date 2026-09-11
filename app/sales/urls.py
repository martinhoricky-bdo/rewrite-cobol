from django.urls import path

from . import views

app_name = "sales"

urlpatterns = [
    path("sell/", views.sell_step1, name="sell_step1"),
    path("sell/passengers/", views.sell_step2, name="sell_step2"),
    path("sell/passenger-name/", views.passenger_name, name="passenger_name"),
    path("buys/<int:buyid>/", views.buy_detail, name="buy_detail"),
    path("passengers/", views.passenger_list, name="passenger_list"),
    path("passengers/new/", views.passenger_create, name="passenger_create"),
    path("passengers/<int:clientid>/", views.passenger_detail, name="passenger_detail"),
    path("passengers/<int:clientid>/edit/", views.passenger_edit, name="passenger_edit"),
    path("flights/", views.flight_search, name="flight_search"),
    path("tickets/", views.ticket_search, name="ticket_search"),
    path(
        "tickets/<str:ticketid>/boarding-pass/",
        views.boarding_pass,
        name="boarding_pass",
    ),
    path("tickets/<str:ticketid>/", views.ticket_detail, name="ticket_detail"),
]
