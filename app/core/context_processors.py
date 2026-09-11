from django.utils import timezone

from accounts.permissions import current_role

from .navigation import menu_for


def header(request):
    role = current_role(request.user)
    employee = getattr(request.user, "employee", None) if request.user.is_authenticated else None
    return {
        "now_local": timezone.localtime(),
        "app_title": "COBOL AIRLINES",
        "app_subtitle": "Programming at heights",
        "employee": employee,
        "role": role.label if role else None,
        "menu": menu_for(request.user),
    }
