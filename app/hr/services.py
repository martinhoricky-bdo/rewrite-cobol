"""Design: employee services implement UC-H01 account creation and SUINSRT-derived EMPID
allocation.
"""

from django.db import transaction

from accounts.services import ensure_user_for_employee


@transaction.atomic
def create_employee(form):
    """Save the employee and create the matching inactive account in one transaction."""
    employee = form.save()
    ensure_user_for_employee(employee)
    return employee
