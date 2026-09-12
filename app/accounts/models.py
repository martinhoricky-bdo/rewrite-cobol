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
    """Represents an application user backed by the legacy EMPLO/DEPT identity and relationship
    rules.
    """

    must_change_password = models.BooleanField(default=False)

    class Meta:
        db_table = "accounts_user"


class Department(models.Model):
    """Represents an application department backed by the legacy EMPLO/DEPT identity and
    relationship rules.
    """

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


class EmployeeQuerySet(models.QuerySet):
    """Provides composable database filters and annotations for employee records used by
    authentication and IT account workflows in UC-A01–A03 and UC-I01.
    """

    def search(self, text):
        """Match employees against their identifier, name, surname, or username."""
        text = text.strip()
        if not text:
            return self
        return self.filter(
            Q(firstname__icontains=text)
            | Q(lastname__icontains=text)
            | Q(dept__name__icontains=text)
        )

    def name_starts_with(self, text):
        """Filter employees whose first name or surname begins with the supplied prefix."""
        text = text.strip()
        if not text:
            return self
        return self.filter(Q(firstname__istartswith=text) | Q(lastname__istartswith=text))

    def in_department(self, deptid):
        """Restrict employees to the selected legacy DEPT identifier."""
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
        db_table = "emplo"
        ordering = ["empid"]

    def __str__(self) -> str:
        return self.full_name

    def get_absolute_url(self) -> str:
        """Build the canonical detail URL used after saving this record for employee."""
        return reverse("hr:employee_detail", kwargs={"empid": self.pk})

    @property
    def role(self) -> str:
        """Derive the authorization role from the employee position linked to this user."""
        return ROLE_BY_DEPT[self.dept_id]

    @property
    def full_name(self) -> str:
        """Combine the employee’s first name and surname for labels and printed documents."""
        return f"{self.firstname} {self.lastname}"
