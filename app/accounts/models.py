"""Account, employee, and department models mapped from the DB2/DCLGEN EMPLO and DEPT
tables; SUINSRT defines employee identifiers.
"""

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse

from .roles import ROLE_BY_DEPT


class User(AbstractUser):
    """Provide User behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""

    must_change_password = models.BooleanField(default=False)

    class Meta:
        """Provide Meta behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""

        db_table = "accounts_user"


class Department(models.Model):
    """Provide Department behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""

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
        """Provide Meta behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""

        db_table = "dept"

    def __str__(self) -> str:
        return self.name


class EmployeeQuerySet(models.QuerySet):
    """Provide EmployeeQuerySet behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""

    def search(self, text):
        """Implement search behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""
        text = text.strip()
        if not text:
            return self
        return self.filter(
            Q(firstname__icontains=text)
            | Q(lastname__icontains=text)
            | Q(dept__name__icontains=text)
        )

    def name_starts_with(self, text):
        """Implement name_starts_with behavior for the LOGIN, EMPLO, and DEPT legacy
        lineage.
        """
        text = text.strip()
        if not text:
            return self
        return self.filter(Q(firstname__istartswith=text) | Q(lastname__istartswith=text))

    def in_department(self, deptid):
        """Implement in_department behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""
        return self.filter(dept_id=deptid) if deptid is not None else self


class Employee(models.Model):
    """Map DB2/DCLGEN EMPLO rows; SUINSRT defines EMPID as 10000000 plus the source id."""

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
    objects = EmployeeQuerySet.as_manager()

    class Meta:
        """Provide Meta behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""

        db_table = "emplo"
        ordering = ["empid"]

    def __str__(self) -> str:
        return self.full_name

    def get_absolute_url(self) -> str:
        """Implement get_absolute_url behavior for the LOGIN, EMPLO, and DEPT legacy
        lineage.
        """
        return reverse("hr:employee_detail", kwargs={"empid": self.pk})

    @property
    def role(self) -> str:
        """Implement role behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""
        return ROLE_BY_DEPT[self.dept_id]

    @property
    def full_name(self) -> str:
        """Implement full_name behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""
        return f"{self.firstname} {self.lastname}"
