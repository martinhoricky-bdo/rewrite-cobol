import pytest
from django.db import connection

from sales.models import Ticket
from sales.services import next_ticket_id, reset_ticket_sequence
from tests.factories import BuyFactory, FlightFactory, PassengerFactory

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def restart_ticket_sequence():
    with connection.cursor() as cursor:
        cursor.execute("ALTER SEQUENCE ticket_ticketid_seq RESTART WITH 1")


def test_next_ticket_id_increments_sequence():
    assert next_ticket_id() == "CB00000001"
    assert next_ticket_id() == "CB00000002"


def test_reset_ticket_sequence_uses_highest_existing_ticket():
    client = PassengerFactory()
    Ticket.objects.create(
        ticketid="CB00000010",
        buy=BuyFactory(client=client),
        client=client,
        flight=FlightFactory(),
        seat="A01",
    )
    reset_ticket_sequence()
    assert next_ticket_id() == "CB00000011"
