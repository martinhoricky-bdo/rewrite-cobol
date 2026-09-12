"""Forms for LOGIN account workflows and Design-based IT account maintenance in UC-A01
through UC-A03 and UC-I01.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from core.forms import FilterForm
from core.messages import E_AUTH_01


class UserFilterForm(FilterForm):
    """Provide UserFilterForm behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""

    q = forms.CharField(required=False, label="Filter by name or department")


class LoginForm(AuthenticationForm):
    """Provide LoginForm behavior for the LOGIN, EMPLO, and DEPT legacy lineage."""

    error_messages = {"invalid_login": E_AUTH_01, "inactive": E_AUTH_01}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"autofocus": True, "maxlength": 8})
