from django.db import models
from django.urls import reverse


class Airport(models.Model):
    airportid = models.CharField(max_length=4, primary_key=True)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=30)
    country = models.CharField(max_length=30)
    zipcode = models.CharField(max_length=15)

    class Meta:
        db_table = "airport"
        ordering = ["airportid"]

    def __str__(self) -> str:
        return f"{self.airportid} — {self.name}"

    def get_absolute_url(self) -> str:
        return reverse("it:airport_edit", kwargs={"airportid": self.pk})


class Airplane(models.Model):
    airplaneid = models.CharField(max_length=8, primary_key=True)
    type = models.CharField(max_length=8)
    numseats = models.PositiveIntegerField()
    totalfuel = models.PositiveIntegerField()

    class Meta:
        db_table = "airplane"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(numseats__gt=0), name="airplane_numseats_positive"
            )
        ]

    def __str__(self) -> str:
        return self.airplaneid

    def get_absolute_url(self) -> str:
        return reverse("it:airplane_edit", kwargs={"airplaneid": self.pk})
