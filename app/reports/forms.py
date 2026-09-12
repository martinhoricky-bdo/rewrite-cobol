from django import forms

from core.forms import FilterForm


class ShiftPeriodFilterForm(FilterForm):
    past = forms.BooleanField(required=False, label="Show past shifts")


class PeriodFilterForm(FilterForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["from"] = forms.DateField(required=False, label="From")
        self.fields["to"] = forms.DateField(required=False, label="To")
