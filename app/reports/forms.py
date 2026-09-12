from django import forms

from core.forms import FilterForm


class ShiftPeriodFilterForm(FilterForm):
    past = forms.BooleanField(required=False, label="Show past shifts")


class PeriodFilterForm(FilterForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        widget = forms.DateInput(attrs={"type": "date"})
        self.fields["from"] = forms.DateField(required=False, label="From", widget=widget)
        self.fields["to"] = forms.DateField(required=False, label="To", widget=widget)
