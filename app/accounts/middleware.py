"""Middleware enforcing the password-change policy that complements the reconstructed LOGIN
authentication flow.
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


class MustChangePasswordMiddleware:
    """Provide MustChangePasswordMiddleware behavior for the LOGIN, EMPLO, and DEPT legacy
    lineage.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        password_path = reverse("accounts:password_change")
        exempt = (password_path, reverse("accounts:logout"), "/static/")
        if (
            request.user.is_authenticated
            and request.user.must_change_password
            and not request.path.startswith(exempt)
        ):
            messages.info(request, "You must change your password before continuing.")
            return redirect(password_path)
        return self.get_response(request)
