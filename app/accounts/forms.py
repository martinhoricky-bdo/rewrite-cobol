"""Forms for LOGIN account workflows and Design-based IT account maintenance in UC-A01
through UC-A03 and UC-I01.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from core.forms import FilterForm
from core.messages import E_AUTH_01


class UserFilterForm(FilterForm):
    """Validates and normalizes user filter input for authentication and IT account workflows
    in UC-A01–A03 and UC-I01, using the field-specific messages declared below.
    """

    q = forms.CharField(required=False, label="Filter by name or department")


class LoginForm(AuthenticationForm):
    """Validates and normalizes login input for authentication and IT account workflows in
    UC-A01–A03 and UC-I01, using the field-specific messages declared below.
    """

    error_messages = {"invalid_login": E_AUTH_01, "inactive": E_AUTH_01}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"autofocus": True, "maxlength": 8})
