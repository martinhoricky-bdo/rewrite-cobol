"""Design: employee services implement UC-H01 account creation and SUINSRT-derived EMPID
allocation.
"""

from django.db import transaction

from accounts.services import ensure_user_for_employee


@transaction.atomic
def create_employee(form):
    """Implement create_employee behavior for Design use cases UC-H01 and UC-H02."""
    employee = form.save()
    ensure_user_for_employee(employee)
    return employee
