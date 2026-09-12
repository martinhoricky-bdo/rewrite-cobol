import math
import secrets
from datetime import timedelta

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from .models import Employee, User

LOGIN_FAILURE_LIMIT = 10
LOGIN_FAILURE_WINDOW = timedelta(minutes=15)


def login_failure_key(username: str, ip_address: str) -> str:
    """Return a stable, non-secret cache key for one login source."""
    return f"login-fail:{username.strip().lower()}:{ip_address}"


def login_block_minutes(username: str, ip_address: str) -> int | None:
    state = cache.get(login_failure_key(username, ip_address))
    if not state or state["count"] < LOGIN_FAILURE_LIMIT:
        return None
    seconds = (state["expires_at"] - timezone.now()).total_seconds()
    return max(1, math.ceil(seconds / 60)) if seconds > 0 else None


def record_login_failure(username: str, ip_address: str) -> None:
    key = login_failure_key(username, ip_address)
    state = cache.get(key)
    if state is None:
        state = {"count": 0, "expires_at": timezone.now() + LOGIN_FAILURE_WINDOW}
    state["count"] += 1
    remaining = max(1, int((state["expires_at"] - timezone.now()).total_seconds()))
    cache.set(key, state, timeout=remaining)


def clear_login_failures(username: str, ip_address: str) -> None:
    cache.delete(login_failure_key(username, ip_address))


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
