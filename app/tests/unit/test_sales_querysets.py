import pytest

from sales.models import Passenger
from tests.factories import PassengerFactory

pytestmark = pytest.mark.django_db


def test_name_filters_are_case_insensitive_prefixes():
    match = PassengerFactory(firstname="Maxime", lastname="Duprat")
    PassengerFactory(firstname="Max", lastname="Martin")
    PassengerFactory(firstname="Anne", lastname="Notduprat")
    assert list(Passenger.objects.filter_by(lastname="duP", firstname="MAX")) == [match]


def test_email_filter_is_case_insensitive_contains():
    match = PassengerFactory(email="Maxime.Duprat@Example.com")
    PassengerFactory(email="other@example.org")
    assert list(Passenger.objects.filter_by(email="DUPRAT@EXAMPLE")) == [match]


def test_clientid_filter_is_exact():
    match = PassengerFactory()
    PassengerFactory()
    assert list(Passenger.objects.filter_by(clientid=match.clientid)) == [match]
