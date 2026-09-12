"""Design: employee services implement UC-H01 account creation and SUINSRT-derived EMPID
allocation.
"""

from django.db import transaction

from accounts.services import ensure_user_for_employee


@transaction.atomic
def create_employee(form):
    """Process create employee for Design employee and department maintenance in UC-H01 and
    UC-H02 according to the rules in this callable.
    """
    employee = form.save()
    ensure_user_for_employee(employee)
    return employee
