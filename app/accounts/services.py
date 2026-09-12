import secrets

from django.db import transaction

from .models import Employee, User


@transaction.atomic
def reset_employee_password(employee: Employee) -> str:
    """Create/enable an employee account and return its temporary password."""
    password = secrets.token_urlsafe(16)[:12]
    user = employee.user
    if user is None:
        user = User.objects.create(username=employee.empid)
        employee.user = user
        employee.save(update_fields=["user"])
    user.set_password(password)
    user.is_active = True
    user.must_change_password = True
    user.save(update_fields=["password", "is_active", "must_change_password"])
    return password
