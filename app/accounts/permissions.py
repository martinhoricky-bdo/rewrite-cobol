from collections.abc import Callable
from functools import wraps

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse

from .roles import Role


def current_role(user) -> Role | None:
    if not user.is_authenticated:
        return None
    try:
        return Role(user.employee.role)
    except (AttributeError, ValueError):
        return None


def role_required(*roles: Role | str):
    allowed = {Role(role) for role in roles}

    def decorator(view: Callable) -> Callable:
        @wraps(view)
        def wrapped(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
            if not request.user.is_superuser and current_role(request.user) not in allowed:
                raise PermissionDenied
            return view(request, *args, **kwargs)

        return wrapped

    return decorator


class RoleRequiredMixin:
    roles: tuple[Role | str, ...] = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
        allowed = {Role(role) for role in self.roles}
        if not request.user.is_superuser and current_role(request.user) not in allowed:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
