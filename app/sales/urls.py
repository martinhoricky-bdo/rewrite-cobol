from django.urls import path

from . import views

app_name = "sales"

urlpatterns = [
    path("flights/", views.flight_search, name="flight_search"),
]
