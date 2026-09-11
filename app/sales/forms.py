from django import forms
from django.core.exceptions import ValidationError

from core.messages import E_FLT_01, E_FLT_02


class FlightSearchForm(forms.Form):
    flightnum = forms.CharField(max_length=6, required=False, label="FLIGHT NUM")
    flightdate = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        error_messages={"invalid": E_FLT_02},
        label="DATE",
        widget=forms.DateInput(attrs={"placeholder": "YYYY-MM-DD"}),
    )
    airportdep = forms.CharField(min_length=3, max_length=4, required=False, label="DEP AIRPORT")
    airportarr = forms.CharField(min_length=3, max_length=4, required=False, label="LAND AIRPORT")

    def clean(self):
        cleaned_data = super().clean()
        field_names = ("flightnum", "flightdate", "airportdep", "airportarr")
        if not any(str(self.data.get(name, "")).strip() for name in field_names):
            raise ValidationError(E_FLT_01)
        return cleaned_data
