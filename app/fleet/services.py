from django.db.models import Q

from core.messages import E_REF_01
from operations.models import Flight

from .models import Airplane, Airport


def delete_airport(airport: Airport) -> str | None:
    count = Flight.objects.filter(Q(airportdep=airport) | Q(airportarr=airport)).count()
    if count:
        return E_REF_01.format(Entity="Airport", n=count, related="flights")
    airport.delete()
    return None


def delete_airplane(airplane: Airplane) -> str | None:
    count = airplane.flights.count()
    if count:
        return E_REF_01.format(Entity="Airplane", n=count, related="flights")
    airplane.delete()
    return None
