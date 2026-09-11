from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect, render

from accounts.permissions import current_role

from .messages import E_AUTH_02
from .navigation import ROLE_HOME


@login_required
def home(request):
    role = current_role(request.user)
    if role is None and request.user.is_superuser:
        return render(request, "core/not_available.html", {"admin_only": True})
    if role is None:
        return render(request, "403.html", status=403)
    if home_url := ROLE_HOME[role]:
        return redirect(home_url)
    return render(request, "core/not_available.html", {"role_label": role.label})


def permission_denied(request, exception=None):
    return render(request, "403.html", {"error_message": E_AUTH_02}, status=403)


def healthz(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse({"status": "error", "db": False}, status=503)
    return JsonResponse({"status": "ok", "db": True})
