from django.db import models


class Role(models.TextChoices):
    CEO = "ceo"
    CREW = "crew"
    HR = "hr"
    IT = "it"
    SALES = "sales"
    LEGAL = "legal"
    SCHEDULE = "schedule"


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
