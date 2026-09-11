import pytest

from tests.factories import (
    AirplaneFactory,
    AirportFactory,
    BuyFactory,
    CrewFactory,
    DepartmentFactory,
    EmployeeFactory,
    FlightFactory,
    PassengerFactory,
    ShiftFactory,
    TicketFactory,
)

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "factory_class",
    [
        DepartmentFactory,
        EmployeeFactory,
        AirportFactory,
        AirplaneFactory,
        CrewFactory,
        ShiftFactory,
        FlightFactory,
        PassengerFactory,
        BuyFactory,
        TicketFactory,
    ],
)
def test_factory_creates_valid_object(factory_class):
    instance = factory_class()
    instance.full_clean()
