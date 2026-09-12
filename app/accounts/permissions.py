"""Role authorization primitives for the reconstructed application use cases and their
CICS-style access boundaries.
"""

from collections.abc import Callable
from functools import wraps

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse

from .roles import Role


def current_role(user) -> Role | None:
    """Implement current_role behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""
    if not user.is_authenticated:
        return None
    try:
        return Role(user.employee.role)
    except (AttributeError, ValueError):
        return None


def check_role(request: HttpRequest, allowed: tuple[Role, ...]) -> HttpResponse | None:
    """Implement check_role behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
    if not request.user.is_superuser and current_role(request.user) not in allowed:
        raise PermissionDenied
    return None


def role_required(*roles: Role | str):
    """Restrict the functional HTMX endpoint; all class-based views use ``RoleRequiredMixin``."""

    allowed = tuple(Role(role) for role in roles)

    def decorator(view: Callable) -> Callable:
        """Implement decorator behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""

        @wraps(view)
        def wrapped(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            """Implement wrapped behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""
            if response := check_role(request, allowed):
                return response
            return view(request, *args, **kwargs)

        return wrapped

    return decorator


class RoleRequiredMixin:
    """Provide RoleRequiredMixin behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""

    allowed_roles: tuple[Role, ...] = ()

    def dispatch(self, request, *args, **kwargs):
        """Implement dispatch behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""
        if response := check_role(request, self.allowed_roles):
            return response
        return super().dispatch(request, *args, **kwargs)
