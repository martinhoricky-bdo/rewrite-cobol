from django.contrib import admin

from .models import Crew, Flight, Shift


@admin.register(Crew)
class CrewAdmin(admin.ModelAdmin):
    list_display = ("crewid", "commander", "copilote", "fachief")
    search_fields = ("crewid", "commander__empid", "commander__lastname")


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ("shiftid", "shiftdate", "begintime", "endtime", "crew")
    search_fields = ("shiftid", "crew__crewid")


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ("flightid", "flightnum", "flightdate", "deptime", "airportdep", "airportarr")
    search_fields = ("flightid", "flightnum", "airportdep__name", "airportarr__name")
