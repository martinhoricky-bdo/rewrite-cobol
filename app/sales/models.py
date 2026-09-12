"""Sales models and query sets map DB2 PASSENGERS, BUY, and TICKET, whose CLIENTID and
TICKETID are identities.
"""

from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Upper
from django.urls import reverse

from accounts.models import Employee
from operations.models import Flight


class PassengerQuerySet(models.QuerySet):
    """Provides composable database filters and annotations for passenger records used by
    passenger and ticket sales workflows in UC-S01–S09.
    """

    def filter_by(self, *, clientid=None, lastname=None, firstname=None, email=None):
        """Filter passengers by the submitted name and identifier criteria."""
        queryset = self
        if clientid is not None:
            queryset = queryset.filter(clientid=clientid)
        if lastname:
            queryset = queryset.filter(lastname__istartswith=lastname)
        if firstname:
            queryset = queryset.filter(firstname__istartswith=firstname)
        if email:
            queryset = queryset.filter(email__icontains=email)
        return queryset.order_by("lastname", "firstname", "clientid")


class Passenger(models.Model):
    """Represents one row from the legacy PASSENGERS table, preserving its identity and
    relational constraints.
    """

    clientid = models.AutoField(primary_key=True)
    firstname = models.CharField(max_length=30)
    lastname = models.CharField(max_length=30)
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=50)
    country = models.CharField(max_length=30)
    zipcode = models.CharField(max_length=15)
    telephone = models.CharField(max_length=18)
    email = models.EmailField(max_length=100)
    objects = PassengerQuerySet.as_manager()

    class Meta:
        db_table = "passengers"
        ordering = ["lastname", "firstname", "clientid"]
        indexes = [
            models.Index(Upper("lastname"), Upper("firstname"), name="passengers_name_upper_idx")
        ]

    def __str__(self) -> str:
        return self.full_name

    def get_absolute_url(self) -> str:
        """Build the canonical detail URL used after saving this record for passenger."""
        return reverse("sales:passenger_detail", kwargs={"clientid": self.pk})

    @property
    def full_name(self) -> str:
        """Combine the stored first name and surname for labels and printed documents for
        passenger.
        """
        return f"{self.firstname} {self.lastname}"


class BuyQuerySet(models.QuerySet):
    """Provides composable database filters and annotations for buy records used by passenger
    and ticket sales workflows in UC-S01–S09.
    """

    def with_related(self):
        """Load the related records needed by the consuming screen without extra queries for buy
        query set.
        """
        return self.select_related("emp", "client").prefetch_related("tickets__client")


class Buy(models.Model):
    """Represents one row from the legacy BUY table, preserving its identity and relational
    constraints.
    """

    buyid = models.AutoField(primary_key=True)
    buydate = models.DateField()
    buytime = models.TimeField()
    price = models.DecimalField(max_digits=7, decimal_places=2)
    emp = models.ForeignKey(Employee, models.PROTECT, db_column="empid", related_name="sales")
    client = models.ForeignKey(Passenger, models.PROTECT, db_column="clientid", related_name="buys")
    objects = BuyQuerySet.as_manager()

    class Meta:
        db_table = "buy"
        indexes = [models.Index(fields=["buydate"], name="buy_buydate_idx")]

    def __str__(self) -> str:
        return f"Buy {self.buyid}"

    def get_absolute_url(self) -> str:
        """Build the canonical detail URL used after saving this record for buy."""
        return reverse("sales:buy_detail", kwargs={"buyid": self.pk})


class TicketQuerySet(models.QuerySet):
    """Provides composable database filters and annotations for ticket records used by
    passenger and ticket sales workflows in UC-S01–S09.
    """

    def with_related(self):
        """Load the related records needed by the consuming screen without extra queries for ticket
        query set.
        """
        return self.select_related(
            "client", "flight", "flight__airportdep", "flight__airportarr", "buy", "buy__emp"
        )

    def for_passenger(self, passenger):
        """Restrict tickets to one passenger while retaining their sale and flight details."""
        return self.filter(client=passenger).order_by(
            "flight__flightdate", "flight__deptime", "ticketid"
        )

    def for_buy(self, buy):
        """Restrict tickets to one purchase for receipt and purchase-detail rendering."""
        return self.filter(buy=buy).order_by("ticketid")


class Ticket(models.Model):
    """Represents one row from the legacy TICKET table, preserving its identity and relational
    constraints.
    """

    ticketid = models.CharField(
        max_length=10, primary_key=True, validators=[RegexValidator(r"^CB\d{8}$")]
    )
    buy = models.ForeignKey(Buy, models.PROTECT, db_column="buyid", related_name="tickets")
    client = models.ForeignKey(
        Passenger, models.PROTECT, db_column="clientid", related_name="tickets"
    )
    flight = models.ForeignKey(Flight, models.PROTECT, db_column="flightid", related_name="tickets")
    seat = models.CharField(max_length=3, validators=[RegexValidator(r"^[A-F]\d{2}$")])
    objects = TicketQuerySet.as_manager()

    class Meta:
        db_table = "ticket"
        constraints = [
            models.UniqueConstraint(fields=["flight", "seat"], name="ticket_flight_seat_uniq"),
            models.UniqueConstraint(fields=["flight", "client"], name="ticket_flight_client_uniq"),
        ]

    def __str__(self) -> str:
        return self.ticketid

    def get_absolute_url(self) -> str:
        """Build the canonical detail URL used after saving this record for ticket."""
        return reverse("sales:ticket_detail", kwargs={"ticketid": self.pk})
