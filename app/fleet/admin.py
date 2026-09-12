"""Admin registrations for the AIRPORT and AIRPLANE reference tables inherited from DB2."""

from django.contrib import admin

from .models import Airplane, Airport


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    """Provide AirportAdmin behavior for the AIRPORT and AIRPLANE tables and Design use
    cases UC-I02/UC-I03.
    """

    list_display = ("airportid", "name", "city", "country")
    search_fields = ("airportid", "name", "city", "country")


@admin.register(Airplane)
class AirplaneAdmin(admin.ModelAdmin):
    """Provide AirplaneAdmin behavior for the AIRPORT and AIRPLANE tables and Design use
    cases UC-I02/UC-I03.
    """

    list_display = ("airplaneid", "type", "numseats", "totalfuel")
    search_fields = ("airplaneid", "type")
