"""Design: reporting period forms support crew UC-C01 and CEO overview UC-E01."""

from django import forms

from core.forms import FilterForm


class ShiftPeriodFilterForm(FilterForm):
    """Validates and normalizes shift period filter input for Design shift and executive
    reporting in UC-C01 and UC-E01, using the field-specific messages declared below.
    """

    past = forms.BooleanField(required=False, label="Show past shifts")


class PeriodFilterForm(FilterForm):
    """Validates and normalizes period filter input for Design shift and executive reporting in
    UC-C01 and UC-E01, using the field-specific messages declared below.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        widget = forms.DateInput(attrs={"type": "date"})
        self.fields["from"] = forms.DateField(required=False, label="From", widget=widget)
        self.fields["to"] = forms.DateField(required=False, label="To", widget=widget)
