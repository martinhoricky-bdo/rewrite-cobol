"""Admin registrations for the AIRPORT and AIRPLANE reference tables inherited from DB2."""

from django.contrib import admin

from .models import Airplane, Airport


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    """Configures the Django administration list, search, and edit controls for airport records."""

    list_display = ("airportid", "name", "city", "country")
    search_fields = ("airportid", "name", "city", "country")


@admin.register(Airplane)
class AirplaneAdmin(admin.ModelAdmin):
    """Configures the Django administration list, search, and edit controls for airplane records."""

    list_display = ("airplaneid", "type", "numseats", "totalfuel")
    search_fields = ("airplaneid", "type")
