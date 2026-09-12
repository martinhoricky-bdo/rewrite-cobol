from django.urls import path

from . import views

app_name = "sales"

urlpatterns = [
    path("sell/", views.SellStep1View.as_view(), name="sell_step1"),
    path("sell/passengers/", views.SellStep2View.as_view(), name="sell_step2"),
    path("sell/passenger-name/", views.passenger_name, name="passenger_name"),
    path("buys/<int:buyid>/", views.BuyDetailView.as_view(), name="buy_detail"),
    path("buys/<int:buyid>/receipt/", views.ReceiptView.as_view(), name="receipt"),
    path(
        "buys/<int:buyid>/boarding-passes/",
        views.BoardingPassesView.as_view(),
        name="boarding_passes",
    ),
    path("passengers/", views.PassengerListView.as_view(), name="passenger_list"),
    path("passengers/new/", views.PassengerCreateView.as_view(), name="passenger_create"),
    path(
        "passengers/<int:clientid>/", views.PassengerDetailView.as_view(), name="passenger_detail"
    ),
    path(
        "passengers/<int:clientid>/edit/",
        views.PassengerUpdateView.as_view(),
        name="passenger_edit",
    ),
    path("flights/", views.FlightSearchView.as_view(), name="flight_search"),
    path("tickets/", views.TicketSearchView.as_view(), name="ticket_search"),
    path(
        "tickets/<str:ticketid>/boarding-pass/",
        views.BoardingPassView.as_view(),
        name="boarding_pass",
    ),
    path("tickets/<str:ticketid>/", views.TicketDetailView.as_view(), name="ticket_detail"),
]
