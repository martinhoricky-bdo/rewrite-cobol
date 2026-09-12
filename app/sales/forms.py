"""Sales forms reconstruct SRCHFLY, SRCHTKT, SELLCOB1, and the missing SELLCOB2 workflows
for UC-S01 through UC-S07.
"""

import re

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from core.forms import FilterForm
from core.messages import (
    E_FLT_01,
    E_FLT_02,
    E_SEL_01,
    E_SEL_02,
    E_SEL_03,
    E_SEL_04,
    E_SEL_11,
    E_TKT_01,
)

from .models import Passenger

TELEPHONE_ERROR = "Telephone may contain digits, spaces, + and - only."
# Sentinel that can never match a real TICKETID; keeps the legacy behaviour
# (wrong format = empty result with E_TKT_02, not a validation error).
INVALID_TICKET_ID = "__invalid__"


class SellStep1Form(forms.Form):
    """Validates and normalizes sell step1 input for passenger and ticket sales workflows in
    UC-S01–S09, using the field-specific messages declared below.
    """

    clientid = forms.IntegerField(
        min_value=1,
        label="CLIENT ID",
        error_messages={"required": E_SEL_01, "invalid": E_SEL_01, "min_value": E_SEL_01},
    )
    flightnum = forms.CharField(
        max_length=6,
        label="FLIGHT NUM",
        error_messages={
            "required": E_SEL_02,
            "invalid": E_SEL_02,
            "max_length": E_SEL_02,
            "null_characters_not_allowed": E_SEL_02,
        },
    )
    flightdate = forms.DateField(
        input_formats=["%Y-%m-%d"],
        label="DATE",
        widget=forms.DateInput(attrs={"placeholder": "YYYY-MM-DD"}),
        error_messages={"required": E_SEL_03, "invalid": E_SEL_03},
    )
    count = forms.IntegerField(
        min_value=1,
        max_value=9,
        label="PASS NUMBER",
        error_messages={
            "required": E_SEL_04,
            "invalid": E_SEL_04,
            "min_value": E_SEL_04,
            "max_value": E_SEL_04,
        },
    )


class SellStep2Form(forms.Form):
    """Validates and normalizes sell step2 input for passenger and ticket sales workflows in
    UC-S01–S09, using the field-specific messages declared below.
    """

    def __init__(self, count, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for number in range(1, count + 1):
            self.fields[f"client_{number}"] = forms.IntegerField(
                min_value=1,
                label="CLIENTID",
                error_messages={
                    "required": E_SEL_01,
                    "invalid": E_SEL_01,
                    "min_value": E_SEL_01,
                },
                widget=forms.NumberInput(
                    attrs={
                        "hx-get": "/sales/sell/passenger-name/",
                        "hx-trigger": "change",
                        "hx-target": f"#name-{number}",
                    }
                ),
            )

    def clean(self):
        """Validate related fields together and attach the applicable domain error messages for
        sell step2 form.
        """
        cleaned_data = super().clean()
        seen = set()
        for client_id in cleaned_data.values():
            if client_id in seen:
                raise ValidationError(E_SEL_11.format(id=client_id))
            seen.add(client_id)
        return cleaned_data

    def rows(self, names):
        """Pair passenger identifiers with travel classes for validation."""
        return [
            {"field": self[f"client_{number}"], "name": names.get(number, "")}
            for number in range(1, len(self.fields) + 1)
        ]


class PassengerFilterForm(FilterForm):
    """Validates and normalizes passenger filter input for passenger and ticket sales workflows
    in UC-S01–S09, using the field-specific messages declared below.
    """

    clientid = forms.IntegerField(min_value=1, required=False, label="CLIENT ID")
    lastname = forms.CharField(max_length=30, required=False, label="LAST NAME")
    firstname = forms.CharField(max_length=30, required=False, label="FIRST NAME")
    email = forms.CharField(max_length=100, required=False, label="EMAIL")


class PassengerForm(forms.ModelForm):
    """Validates and normalizes passenger input for passenger and ticket sales workflows in
    UC-S01–S09, using the field-specific messages declared below.
    """

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
        """Validate related fields together and attach the applicable domain error messages for
        passenger form.
        """
        cleaned_data = super().clean()
        for field_name in self.Meta.fields:
            value = cleaned_data.get(field_name)
            if isinstance(value, str):
                cleaned_data[field_name] = value.strip()
        return cleaned_data


class FlightSearchForm(forms.Form):
    """Validates and normalizes flight search input for passenger and ticket sales workflows in
    UC-S01–S09, using the field-specific messages declared below.
    """

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
        """Validate related fields together and attach the applicable domain error messages for
        flight search form.
        """
        cleaned_data = super().clean()
        field_names = ("flightnum", "flightdate", "airportdep", "airportarr")
        if not any(str(self.data.get(name, "")).strip() for name in field_names):
            raise ValidationError(E_FLT_01)
        return cleaned_data


class TicketSearchForm(forms.Form):
    """Validates and normalizes ticket search input for passenger and ticket sales workflows in
    UC-S01–S09, using the field-specific messages declared below.
    """

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

    def clean_ticketid(self):
        """Reject a ticket search identifier unless it is a numeric value."""
        ticketid = self.cleaned_data["ticketid"]
        if ticketid and not re.fullmatch(r"CB\d{8}", ticketid, re.IGNORECASE):
            return INVALID_TICKET_ID
        return ticketid

    def clean(self):
        """Validate related fields together and attach the applicable domain error messages for
        ticket search form.
        """
        cleaned_data = super().clean()
        if not (
            cleaned_data.get("ticketid")
            or cleaned_data.get("clientid")
            or (cleaned_data.get("firstname") and cleaned_data.get("lastname"))
        ):
            raise ValidationError(E_TKT_01)
        return cleaned_data
