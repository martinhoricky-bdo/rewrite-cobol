from datetime import time
from decimal import Decimal

import factory
from factory.django import DjangoModelFactory

from accounts.models import Department, Employee, User
from fleet.models import Airplane, Airport
from operations.models import Crew, Flight, Shift
from sales.models import Buy, Passenger, Ticket
from sales.services import next_ticket_id


class DepartmentFactory(DjangoModelFactory):
    class Meta:
        model = Department
        django_get_or_create = ("deptid",)

    deptid = factory.Sequence(lambda n: n + 1)
    name = factory.Sequence(lambda n: f"Department {n + 1}")


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"1000{n:04d}")

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        password = extracted or f"pw-{self.username}"
        self.set_password(password)
        if create:
            self.save(update_fields=["password"])


class EmployeeFactory(DjangoModelFactory):
    class Meta:
        model = Employee

    empid = factory.Sequence(lambda n: f"{10000001 + n:08d}")
    firstname = factory.Faker("first_name")
    lastname = factory.Faker("last_name")
    addre = factory.Faker("street_address")
    city = factory.Faker("city")
    zipcode = factory.Faker("postcode")
    telephone = factory.Sequence(lambda n: f"+331000{n:05d}")
    email = factory.Sequence(lambda n: f"employee{n}@example.com")
    admidate = factory.Faker("date_object")
    salary = Decimal("50000.00")
    dept = factory.SubFactory(DepartmentFactory)

    class Params:
        with_user = factory.Trait(user=factory.SubFactory(UserFactory))


class AirportFactory(DjangoModelFactory):
    class Meta:
        model = Airport

    airportid = factory.Sequence(
        lambda n: f"{chr(65 + (n // 676) % 26)}{chr(65 + (n // 26) % 26)}{chr(65 + n % 26)}"
    )
    name = factory.Sequence(lambda n: f"Airport {n}")
    address = factory.Faker("street_address")
    city = factory.Faker("city")
    country = "France"
    zipcode = factory.Faker("postcode")


class AirplaneFactory(DjangoModelFactory):
    class Meta:
        model = Airplane

    airplaneid = factory.Sequence(lambda n: f"PL{n:06d}")
    type = "A320"
    numseats = 150
    totalfuel = 24000


class CrewFactory(DjangoModelFactory):
    class Meta:
        model = Crew

    commander = factory.SubFactory(EmployeeFactory)
    copilote = factory.SubFactory(EmployeeFactory)
    fachief = factory.SubFactory(EmployeeFactory)
    fliattendant1 = factory.SubFactory(EmployeeFactory)
    fliattendant2 = factory.SubFactory(EmployeeFactory)
    fliattendant3 = factory.SubFactory(EmployeeFactory)


class ShiftFactory(DjangoModelFactory):
    class Meta:
        model = Shift

    shiftdate = factory.Faker("date_object")
    begintime = time(8)
    endtime = time(16)
    crew = factory.SubFactory(CrewFactory)


class FlightFactory(DjangoModelFactory):
    class Meta:
        model = Flight

    flightdate = factory.Faker("future_date")
    deptime = time(10)
    arrtime = time(12)
    flightnum = factory.Sequence(lambda n: f"CB{n:04d}")
    shift = factory.SubFactory(ShiftFactory)
    airplane = factory.SubFactory(AirplaneFactory)
    airportdep = factory.SubFactory(AirportFactory)
    airportarr = factory.SubFactory(AirportFactory)
    price = Decimal("120.99")
    totpass = factory.LazyAttribute(lambda obj: obj.airplane.numseats)
    totbagga = 0


class PassengerFactory(DjangoModelFactory):
    class Meta:
        model = Passenger

    firstname = factory.Faker("first_name")
    lastname = factory.Faker("last_name")
    address = factory.Faker("street_address")
    city = factory.Faker("city")
    country = "France"
    zipcode = factory.Faker("postcode")
    telephone = factory.Sequence(lambda n: f"+332000{n:05d}")
    email = factory.Sequence(lambda n: f"passenger{n}@example.com")


class BuyFactory(DjangoModelFactory):
    class Meta:
        model = Buy

    buydate = factory.Faker("date_object")
    buytime = time(9)
    price = Decimal("120.99")
    emp = factory.SubFactory(EmployeeFactory)
    client = factory.SubFactory(PassengerFactory)


class TicketFactory(DjangoModelFactory):
    class Meta:
        model = Ticket

    ticketid = factory.LazyFunction(next_ticket_id)
    buy = factory.SubFactory(BuyFactory)
    client = factory.SelfAttribute("buy.client")
    flight = factory.SubFactory(FlightFactory)
    seat = factory.Sequence(lambda n: f"{chr(65 + (n // 99) % 6)}{n % 99 + 1:02d}")
