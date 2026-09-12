"""Admin registrations for the legacy DB2 PASSENGERS, BUY, and TICKET sales tables."""

from django.contrib import admin

from .models import Buy, Passenger, Ticket


@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    """Configures the Django administration list, search, and edit controls for passenger
    records.
    """

    list_display = ("clientid", "firstname", "lastname", "email", "city")
    search_fields = ("clientid", "firstname", "lastname", "email")


@admin.register(Buy)
class BuyAdmin(admin.ModelAdmin):
    """Configures the Django administration list, search, and edit controls for buy records."""

    list_display = ("buyid", "buydate", "buytime", "client", "emp", "price")
    search_fields = ("buyid", "client__firstname", "client__lastname", "emp__empid")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """Configures the Django administration list, search, and edit controls for ticket records."""

    list_display = ("ticketid", "flight", "client", "seat", "buy")
    search_fields = ("ticketid", "flight__flightnum", "client__firstname", "client__lastname")
