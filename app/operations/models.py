from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from accounts.models import Employee
from fleet.models import Airplane, Airport


class Crew(models.Model):
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

    class Meta:
        db_table = "crew"

    def __str__(self) -> str:
        return f"Crew {self.crewid}"

    def members(self) -> list[Employee]:
        return [
            self.commander,
            self.copilote,
            self.fachief,
            self.fliattendant1,
            self.fliattendant2,
            self.fliattendant3,
        ]

    def clean(self) -> None:
        super().clean()
        member_ids = [member.pk for member in self.members()]
        if len(set(member_ids)) != len(member_ids):
            raise ValidationError("Crew members must be unique.")


class Shift(models.Model):
    shiftid = models.AutoField(primary_key=True)
    shiftdate = models.DateField()
    begintime = models.TimeField()
    endtime = models.TimeField()
    crew = models.ForeignKey(Crew, models.PROTECT, db_column="crewid", related_name="shifts")

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


class Flight(models.Model):
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
