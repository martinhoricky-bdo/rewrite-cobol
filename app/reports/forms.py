"""Design: reporting period forms support crew UC-C01 and CEO overview UC-E01."""

from django import forms

from core.forms import FilterForm


class ShiftPeriodFilterForm(FilterForm):
    """Provide ShiftPeriodFilterForm behavior for Design use cases UC-C01 and UC-E01."""

    past = forms.BooleanField(required=False, label="Show past shifts")


class PeriodFilterForm(FilterForm):
    """Provide PeriodFilterForm behavior for Design use cases UC-C01 and UC-E01."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        widget = forms.DateInput(attrs={"type": "date"})
        self.fields["from"] = forms.DateField(required=False, label="From", widget=widget)
        self.fields["to"] = forms.DateField(required=False, label="To", widget=widget)
