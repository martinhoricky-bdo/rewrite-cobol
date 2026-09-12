"""Operational models and query sets map the legacy DB2 FLIGHT, CREW, and SHIFT tables."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Count, Q
from django.urls import reverse

from accounts.models import Employee
from fleet.models import Airplane, Airport


class CrewQuerySet(models.QuerySet):
    """Provides composable database filters and annotations for crew records used by Design
    scheduling workflows in UC-P01–P04.
    """

    def with_member(self, employee):
        """Filter crews containing the selected employee in any crew position."""
        return self.filter(
            Q(commander=employee)
            | Q(copilote=employee)
            | Q(fachief=employee)
            | Q(fliattendant1=employee)
            | Q(fliattendant2=employee)
            | Q(fliattendant3=employee)
        ).distinct()

    def with_shift_count(self):
        """Annotate each crew with its assigned shift count and restore deterministic ordering."""
        return self.annotate(shift_count=Count("shifts"))

    def with_members(self):
        """Select all employee relations required to display a crew without repeated queries."""
        return self.select_related(
            "commander", "copilote", "fachief", "fliattendant1", "fliattendant2", "fliattendant3"
        )


class Crew(models.Model):
    """Represents one row from the legacy CREW table, including the scheduling relationships
    and constraints declared below.
    """

    crewid = models.AutoField(primary_key=True)
    commander = models.ForeignKey(
        Employee, models.PROTECT, db_column="commander", related_name="crews_as_commander"
    )
    copilote = models.ForeignKey(
        Employee, models.PROTECT, db_column="copilote", related_name="crews_as_copilote"
    )
    fachief = models.ForeignKey(
        Employee, models.PROTECT, db_column="fachief", related_name="crews_as_fachief"
    )
    fliattendant1 = models.ForeignKey(
        Employee,
        models.PROTECT,
        db_column="fliattendant1",
        related_name="crews_as_fliattendant1",
    )
    fliattendant2 = models.ForeignKey(
        Employee,
        models.PROTECT,
        db_column="fliattendant2",
        related_name="crews_as_fliattendant2",
    )
    fliattendant3 = models.ForeignKey(
        Employee,
        models.PROTECT,
        db_column="fliattendant3",
        related_name="crews_as_fliattendant3",
    )
    objects = CrewQuerySet.as_manager()

    class Meta:
        db_table = "crew"

    def __str__(self) -> str:
        return f"Crew {self.crewid}"

    def get_absolute_url(self) -> str:
        """Return the schedule edit URL of this crew."""
        return reverse("schedule:crew_edit", kwargs={"crewid": self.pk})

    def members(self) -> list[Employee]:
        """List the captain and attendants in the operational display order."""
        return [
            self.commander,
            self.copilote,
            self.fachief,
            self.fliattendant1,
            self.fliattendant2,
            self.fliattendant3,
        ]

    def clean(self) -> None:
        """Refuse a crew whose six positions are not held by six different employees."""
        super().clean()
        member_ids = [
            self.commander_id,
            self.copilote_id,
            self.fachief_id,
            self.fliattendant1_id,
            self.fliattendant2_id,
            self.fliattendant3_id,
        ]
        present_ids = [member_id for member_id in member_ids if member_id is not None]
        if len(set(present_ids)) != len(present_ids):
            raise ValidationError("Crew members must be unique.")


class ShiftQuerySet(models.QuerySet):
    """Provides composable database filters and annotations for shift records used by Design
    scheduling workflows in UC-P01–P04.
    """

    def in_period(self, date_from, date_to):
        """Restrict the shifts to the inclusive date range."""
        return self.filter(shiftdate__range=(date_from, date_to))

    def with_flight_count(self):
        """Annotate shifts with their flight totals and restore deterministic ordering."""
        return self.annotate(flight_count=Count("flights"))

    def for_crew(self, crew_id):
        """Restrict shifts to those assigned to the selected crew."""
        return self.filter(crew_id=crew_id) if crew_id is not None else self


class Shift(models.Model):
    """Represents one row from the legacy SHIFT table, including the scheduling relationships
    and constraints declared below.
    """

    shiftid = models.AutoField(primary_key=True)
    shiftdate = models.DateField()
    begintime = models.TimeField()
    endtime = models.TimeField()
    crew = models.ForeignKey(Crew, models.PROTECT, db_column="crewid", related_name="shifts")
    objects = ShiftQuerySet.as_manager()

    class Meta:
        db_table = "shift"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(begintime__lt=models.F("endtime")),
                name="shift_begin_before_end",
            )
        ]
        indexes = [models.Index(fields=["shiftdate"], name="shift_shiftdate_idx")]

    def __str__(self) -> str:
        return f"Shift {self.shiftid} ({self.shiftdate})"

    def get_absolute_url(self) -> str:
        """Return the schedule edit URL of this shift."""
        return reverse("schedule:shift_edit", kwargs={"shiftid": self.pk})


class FlightQuerySet(models.QuerySet):
    """Provides composable database filters and annotations for flight records used by Design
    scheduling workflows in UC-P01–P04.
    """

    def with_sold(self):
        """Annotate flights with sold-ticket totals and restore deterministic ordering."""
        return self.annotate(sold=Count("tickets"))

    def in_period(self, date_from, date_to):
        """Restrict the flights to the inclusive date range."""
        return self.filter(flightdate__range=(date_from, date_to))

    def with_related(self):
        """Join the airports, the airplane and the shift shown in the flight lists."""
        return self.select_related("airportdep", "airportarr", "airplane", "shift")


class Flight(models.Model):
    """Represents one row from the legacy FLIGHT table, including the scheduling relationships
    and constraints declared below.
    """

    flightid = models.AutoField(primary_key=True)
    flightdate = models.DateField()
    deptime = models.TimeField()
    arrtime = models.TimeField()
    totpass = models.IntegerField()
    totbagga = models.IntegerField(default=0)
    flightnum = models.CharField(max_length=6, validators=[RegexValidator(r"^CB\d{4}$")])
    shift = models.ForeignKey(Shift, models.PROTECT, db_column="shiftid", related_name="flights")
    airplane = models.ForeignKey(
        Airplane, models.PROTECT, db_column="airplaneid", related_name="flights"
    )
    airportdep = models.ForeignKey(
        Airport, models.PROTECT, db_column="airportdep", related_name="departures"
    )
    airportarr = models.ForeignKey(
        Airport, models.PROTECT, db_column="airportarr", related_name="arrivals"
    )
    price = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("120.99"))
    objects = FlightQuerySet.as_manager()

    class Meta:
        db_table = "flight"
        ordering = ["flightdate", "deptime", "flightnum"]
        constraints = [
            models.UniqueConstraint(
                fields=["flightnum", "flightdate"],
                name="flight_flightnum_flightdate_uniq",
            ),
            models.CheckConstraint(
                condition=~models.Q(airportdep=models.F("airportarr")),
                name="flight_airports_differ",
            ),
        ]
        indexes = [
            models.Index(fields=["flightdate", "deptime"], name="flight_date_deptime_idx"),
            models.Index(fields=["flightnum"], name="flight_flightnum_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.flightnum} {self.flightdate}"

    def get_absolute_url(self) -> str:
        """Return the schedule edit URL of this flight."""
        return reverse("schedule:flight_edit", kwargs={"flightid": self.pk})
