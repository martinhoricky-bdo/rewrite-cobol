from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Upper

from accounts.models import Employee
from operations.models import Flight


class Passenger(models.Model):
    clientid = models.AutoField(primary_key=True)
    firstname = models.CharField(max_length=30)
    lastname = models.CharField(max_length=30)
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=50)
    country = models.CharField(max_length=30)
    zipcode = models.CharField(max_length=15)
    telephone = models.CharField(max_length=18)
    email = models.EmailField(max_length=100)

    class Meta:
        db_table = "passengers"
        ordering = ["lastname", "firstname", "clientid"]
        indexes = [
            models.Index(Upper("lastname"), Upper("firstname"), name="passengers_name_upper_idx")
        ]

    def __str__(self) -> str:
        return self.full_name

    @property
    def full_name(self) -> str:
        return f"{self.firstname} {self.lastname}"


class Buy(models.Model):
    buyid = models.AutoField(primary_key=True)
    buydate = models.DateField()
    buytime = models.TimeField()
    price = models.DecimalField(max_digits=7, decimal_places=2)
    emp = models.ForeignKey(Employee, models.PROTECT, db_column="empid", related_name="sales")
    client = models.ForeignKey(Passenger, models.PROTECT, db_column="clientid", related_name="buys")

    class Meta:
        db_table = "buy"
        indexes = [models.Index(fields=["buydate"], name="buy_buydate_idx")]

    def __str__(self) -> str:
        return f"Buy {self.buyid}"


class Ticket(models.Model):
    ticketid = models.CharField(
        max_length=10, primary_key=True, validators=[RegexValidator(r"^CB\d{8}$")]
    )
    buy = models.ForeignKey(Buy, models.PROTECT, db_column="buyid", related_name="tickets")
    client = models.ForeignKey(
        Passenger, models.PROTECT, db_column="clientid", related_name="tickets"
    )
    flight = models.ForeignKey(Flight, models.PROTECT, db_column="flightid", related_name="tickets")
    seat = models.CharField(max_length=3, validators=[RegexValidator(r"^[A-F]\d{2}$")])

    class Meta:
        db_table = "ticket"
        constraints = [
            models.UniqueConstraint(fields=["flight", "seat"], name="ticket_flight_seat_uniq"),
            models.UniqueConstraint(fields=["flight", "client"], name="ticket_flight_client_uniq"),
        ]

    def __str__(self) -> str:
        return self.ticketid
