from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from .roles import ROLE_BY_DEPT


class User(AbstractUser):
    class Meta:
        db_table = "accounts_user"


class Department(models.Model):
    deptid = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=20)
    manager = models.ForeignKey(
        "Employee",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="manager",
        related_name="managed_departments",
    )

    class Meta:
        db_table = "dept"

    def __str__(self) -> str:
        return self.name


class Employee(models.Model):
    empid = models.CharField(
        max_length=8,
        primary_key=True,
        validators=[RegexValidator(r"^\d{8}$")],
    )
    firstname = models.CharField(max_length=30)
    lastname = models.CharField(max_length=30)
    addre = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    zipcode = models.CharField(max_length=15)
    telephone = models.CharField(max_length=20)
    email = models.EmailField(max_length=100)
    admidate = models.DateField()
    salary = models.DecimalField(max_digits=8, decimal_places=2)
    dept = models.ForeignKey(
        Department, on_delete=models.PROTECT, db_column="deptid", related_name="employees"
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="user_id",
        related_name="employee",
    )

    class Meta:
        db_table = "emplo"
        ordering = ["empid"]

    def __str__(self) -> str:
        return self.full_name

    @property
    def role(self) -> str:
        return ROLE_BY_DEPT[self.dept_id]

    @property
    def full_name(self) -> str:
        return f"{self.firstname} {self.lastname}"
