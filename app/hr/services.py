from django.db import transaction

from accounts.services import ensure_user_for_employee


@transaction.atomic
def create_employee(form):
    employee = form.save()
    ensure_user_for_employee(employee)
    return employee
