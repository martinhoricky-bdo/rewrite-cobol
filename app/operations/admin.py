"""Admin registrations for the DB2 FLIGHT, CREW, and SHIFT operational tables."""

from django.contrib import admin

from .models import Crew, Flight, Shift


@admin.register(Crew)
class CrewAdmin(admin.ModelAdmin):
    """Configures the Django administration list, search, and edit controls for crew records."""

    list_display = ("crewid", "commander", "copilote", "fachief")
    search_fields = ("crewid", "commander__empid", "commander__lastname")


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    """Configures the Django administration list, search, and edit controls for shift records."""

    list_display = ("shiftid", "shiftdate", "begintime", "endtime", "crew")
    search_fields = ("shiftid", "crew__crewid")


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    """Configures the Django administration list, search, and edit controls for flight records."""

    list_display = ("flightid", "flightnum", "flightdate", "deptime", "airportdep", "airportarr")
    search_fields = ("flightid", "flightnum", "airportdep__name", "airportarr__name")
