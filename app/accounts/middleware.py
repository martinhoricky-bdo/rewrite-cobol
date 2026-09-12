"""Middleware enforcing the password-change policy that complements the reconstructed LOGIN
authentication flow.
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


class MustChangePasswordMiddleware:
    """Encapsulates must change password middleware responsibilities required by authentication
    and IT account workflows in UC-A01–A03 and UC-I01, with constraints declared on its
    fields.
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
