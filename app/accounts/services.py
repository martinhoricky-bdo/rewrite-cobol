import secrets

from django.db import transaction

from .models import Employee, User


@transaction.atomic
def ensure_user_for_employee(employee: Employee) -> User:
    """Ensure an employee has an inactive account with an unusable initial password."""
    if employee.user_id:
        return employee.user
    user, created = User.objects.get_or_create(username=employee.empid)
    if created:
        user.is_active = False
        user.set_unusable_password()
        user.save(update_fields=["is_active", "password"])
    employee.user = user
    employee.save(update_fields=["user"])
    return user


@transaction.atomic
def reset_employee_password(employee: Employee) -> str:
    """Create/enable an employee account and return its temporary password."""
    password = secrets.token_urlsafe(16)[:12]
    user = ensure_user_for_employee(employee)
    user.set_password(password)
    user.is_active = True
    user.must_change_password = True
    user.save(update_fields=["password", "is_active", "must_change_password"])
    return password
