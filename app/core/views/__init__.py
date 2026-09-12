from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import connection
from django.http import HttpResponseServerError, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.views import View

from accounts.permissions import current_role
from core.exceptions import NotFound
from core.messages import E_AUTH_02
from core.navigation import ROLE_HOME


class HomeView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        role = current_role(self.request.user)
        if role is None and self.request.user.is_superuser:
            return render(self.request, "core/not_available.html", {"admin_only": True})
        if role is None:
            return render(self.request, "403.html", status=403)
        if home_url := ROLE_HOME[role]:
            return redirect(home_url)
        return render(self.request, "core/not_available.html", {"role_label": role.label})


def permission_denied(request, exception=None):
    return render(request, "403.html", {"error_message": E_AUTH_02}, status=403)


def page_not_found(request, exception=None):
    context = {"error_message": exception.message} if isinstance(exception, NotFound) else {}
    return render(request, "404.html", context, status=404)


def server_error(request):
    # Rendered without request context so a failing context processor cannot break this page.
    return HttpResponseServerError(render_to_string("500.html"))


def healthz(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse({"status": "error", "db": False}, status=503)
    return JsonResponse({"status": "ok", "db": True})
