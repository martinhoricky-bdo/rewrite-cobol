from django.db import models


class Role(models.TextChoices):
    CEO = "ceo", "CEO"
    CREW = "crew", "Crew"
    HR = "hr", "HR"
    IT = "it", "IT"
    SALES = "sales", "Sales"
    LEGAL = "legal", "Legal"
    SCHEDULE = "schedule", "Schedule"


ROLE_BY_DEPT = {
    1: Role.CEO,
    2: Role.CREW,
    3: Role.CREW,
    4: Role.CREW,
    5: Role.HR,
    6: Role.IT,
    7: Role.SALES,
    8: Role.LEGAL,
    9: Role.SCHEDULE,
}
