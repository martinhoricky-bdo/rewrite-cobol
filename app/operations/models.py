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
    """Provide CrewQuerySet behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT legacy
    lineage.
    """

    def with_member(self, employee):
        """Implement with_member behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT legacy
        lineage.
        """
        return self.filter(
            Q(commander=employee)
            | Q(copilote=employee)
            | Q(fachief=employee)
            | Q(fliattendant1=employee)
            | Q(fliattendant2=employee)
            | Q(fliattendant3=employee)
        ).distinct()

    def with_shift_count(self):
        """Implement with_shift_count behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT
        legacy lineage.
        """
        return self.annotate(shift_count=Count("shifts"))

    def with_members(self):
        """Implement with_members behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT legacy
        lineage.
        """
        return self.select_related(
            "commander", "copilote", "fachief", "fliattendant1", "fliattendant2", "fliattendant3"
        )


class Crew(models.Model):
    """Provide Crew behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT legacy lineage."""

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
        """Provide Meta behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT legacy lineage."""

        db_table = "crew"

    def __str__(self) -> str:
        return f"Crew {self.crewid}"

    def get_absolute_url(self) -> str:
        """Implement get_absolute_url behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT
        legacy lineage.
        """
        return reverse("schedule:crew_edit", kwargs={"crewid": self.pk})

    def members(self) -> list[Employee]:
        """Implement members behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT legacy
        lineage.
        """
        return [
            self.commander,
            self.copilote,
            self.fachief,
            self.fliattendant1,
            self.fliattendant2,
            self.fliattendant3,
        ]

    def clean(self) -> None:
        """Implement clean behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT legacy
        lineage.
        """
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
    """Provide ShiftQuerySet behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT legacy
    lineage.
    """

    def in_period(self, date_from, date_to):
        """Implement in_period behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT legacy
        lineage.
        """
        return self.filter(shiftdate__range=(date_from, date_to))

    def with_flight_count(self):
        """Implement with_flight_count behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT
        legacy lineage.
        """
        return self.annotate(flight_count=Count("flights"))

    def for_crew(self, crew_id):
        """Implement for_crew behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT legacy
        lineage.
        """
        return self.filter(crew_id=crew_id) if crew_id is not None else self


class Shift(models.Model):
    """Provide Shift behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT legacy lineage."""

    shiftid = models.AutoField(primary_key=True)
    shiftdate = models.DateField()
    begintime = models.TimeField()
    endtime = models.TimeField()
    crew = models.ForeignKey(Crew, models.PROTECT, db_column="crewid", related_name="shifts")
    objects = ShiftQuerySet.as_manager()

    class Meta:
        """Provide Meta behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT legacy lineage."""

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
        """Implement get_absolute_url behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT
        legacy lineage.
        """
        return reverse("schedule:shift_edit", kwargs={"shiftid": self.pk})


class FlightQuerySet(models.QuerySet):
    """Provide FlightQuerySet behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT legacy
    lineage.
    """

    def with_sold(self):
        """Implement with_sold behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT legacy
        lineage.
        """
        return self.annotate(sold=Count("tickets"))

    def in_period(self, date_from, date_to):
        """Implement in_period behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT legacy
        lineage.
        """
        return self.filter(flightdate__range=(date_from, date_to))

    def with_related(self):
        """Implement with_related behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT legacy
        lineage.
        """
        return self.select_related("airportdep", "airportarr", "airplane", "shift")


class Flight(models.Model):
    """Provide Flight behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT legacy lineage."""

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
        """Provide Meta behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT legacy lineage."""

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
        """Implement get_absolute_url behavior for the FLIGHT, CREW, SHIFT, and CBFLIGHT
        legacy lineage.
        """
        return reverse("schedule:flight_edit", kwargs={"flightid": self.pk})
