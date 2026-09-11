from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from core.messages import E_FLT_01, E_FLT_02, E_TKT_01

from .models import Passenger

TELEPHONE_ERROR = "Telephone may contain digits, spaces, + and - only."


class PassengerFilterForm(forms.Form):
    clientid = forms.IntegerField(min_value=1, required=False, label="CLIENT ID")
    lastname = forms.CharField(max_length=30, required=False, label="LAST NAME")
    firstname = forms.CharField(max_length=30, required=False, label="FIRST NAME")
    email = forms.CharField(max_length=100, required=False, label="EMAIL")


class PassengerForm(forms.ModelForm):
    telephone = forms.CharField(
        max_length=18,
        validators=[RegexValidator(r"^[0-9 +\-]{1,18}$", TELEPHONE_ERROR)],
        label="TELEPHONE",
    )
    email = forms.EmailField(max_length=100, label="EMAIL")

    class Meta:
        model = Passenger
        fields = (
            "firstname",
            "lastname",
            "address",
            "city",
            "country",
            "zipcode",
            "telephone",
            "email",
        )

    def clean(self):
        cleaned_data = super().clean()
        for field_name in self.Meta.fields:
            value = cleaned_data.get(field_name)
            if isinstance(value, str):
                cleaned_data[field_name] = value.strip()
        return cleaned_data


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


class TicketSearchForm(forms.Form):
    ticketid = forms.CharField(max_length=10, required=False, label="TICKET ID")
    clientid = forms.IntegerField(min_value=1, required=False, label="CLIENT ID")
    firstname = forms.CharField(max_length=30, required=False, label="FIRST NAME")
    lastname = forms.CharField(max_length=30, required=False, label="LAST NAME")
    flightnum = forms.CharField(max_length=6, required=False, label="FLIGHT NUM")
    flightdate = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        error_messages={"invalid": E_FLT_02},
        label="FLIGHT DATE",
        widget=forms.DateInput(attrs={"placeholder": "YYYY-MM-DD"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        if not (
            cleaned_data.get("ticketid")
            or cleaned_data.get("clientid")
            or (cleaned_data.get("firstname") and cleaned_data.get("lastname"))
        ):
            raise ValidationError(E_TKT_01)
        return cleaned_data
