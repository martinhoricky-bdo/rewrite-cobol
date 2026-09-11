from django.contrib import admin

from .models import Airplane, Airport


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ("airportid", "name", "city", "country")
    search_fields = ("airportid", "name", "city", "country")


@admin.register(Airplane)
class AirplaneAdmin(admin.ModelAdmin):
    list_display = ("airplaneid", "type", "numseats", "totalfuel")
    search_fields = ("airplaneid", "type")
