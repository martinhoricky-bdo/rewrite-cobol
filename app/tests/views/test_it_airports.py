import pytest
from django.urls import reverse

from accounts.roles import Role
from core.messages import E_REF_01
from fleet.models import Airport
from tests.factories import FlightFactory

pytestmark = pytest.mark.django_db


def airport_data(identifier="cdg"):
    return {
        "airportid": identifier,
        "name": "Charles",
        "address": "1 Road",
        "city": "Paris",
        "country": "France",
        "zipcode": "75000",
    }


def test_airport_crud_uppercase_and_validation(role_client):
    client = role_client(Role.IT)
    response = client.post(reverse("it:airport_create"), airport_data())
    assert response.status_code == 302
    assert Airport.objects.filter(pk="CDG").exists()
    response = client.post(reverse("it:airport_create"), airport_data())
    assert response.status_code == 200
    assert "already exists" in response.content.decode()
    response = client.post(reverse("it:airport_create"), airport_data("12"))
    assert "letters (A–Z)" in response.content.decode()
    response = client.post(reverse("it:airport_create"), airport_data("ABCDE"))
    assert response.status_code == 200
    assert "at most 4 characters" in response.content.decode()
    assert not Airport.objects.filter(pk="ABCDE").exists()


def test_invalid_airport_create_reports_error_without_writing(role_client):
    client = role_client(Role.IT)
    before = Airport.objects.count()

    response = client.post(reverse("it:airport_create"), airport_data("ABCDE"))

    assert response.status_code == 200
    assert "Ensure this value has at most 4 characters" in response.content.decode()
    assert Airport.objects.count() == before


def test_airport_delete_reference(role_client):
    client = role_client(Role.SCHEDULE)
    flight = FlightFactory()
    url = reverse("it:airport_delete", args=[flight.airportdep_id])
    response = client.post(url, follow=True)
    assert E_REF_01.format(Entity="Airport", n=1, related="flights") in response.content.decode()
    assert Airport.objects.filter(pk=flight.airportdep_id).exists()
    unused = Airport.objects.create(
        airportid="ORY", name="Orly", address="Road", city="Paris", country="France", zipcode="1"
    )
    client.post(reverse("it:airport_delete", args=[unused.pk]))
    assert not Airport.objects.filter(pk="ORY").exists()


@pytest.mark.parametrize("role", [Role.IT, Role.SCHEDULE])
def test_it_and_schedule_can_view_airports(role_client, role):
    client = role_client(role)
    assert client.get(reverse("it:airports")).status_code == 200
