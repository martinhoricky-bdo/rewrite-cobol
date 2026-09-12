"""Context processors reproduce the CICS map header fields USERID, TERMINAL, DATE, TIME,
MSG1, and MSG2 in base.html.
"""

from django.utils import timezone

from accounts.permissions import current_role

from .navigation import menu_for


def header(request):
    """Supply the authenticated user and CICS-style date, time, terminal, and message header
    values.
    """
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
