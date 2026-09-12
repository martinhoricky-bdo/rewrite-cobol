import re

from django import forms
from django.db.models import Count

from .models import Airplane, Airport


class UppercaseIdentifierModelForm(forms.ModelForm):
    identifier_field = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields[self.identifier_field].disabled = True

    def clean_identifier(
        self, value: str, *, minimum: int, maximum: int, letters_only: bool = True
    ) -> str:
        value = value.strip().upper()
        pattern = r"[A-Z]+" if letters_only else r"[A-Z0-9]+"
        if not minimum <= len(value) <= maximum or not re.fullmatch(pattern, value):
            raise forms.ValidationError(
                f"Enter {minimum}–{maximum} letters (A–Z)."
                if minimum != maximum
                else f"Enter {minimum} letters (A–Z)."
            )
        return value


class AirportForm(UppercaseIdentifierModelForm):
    identifier_field = "airportid"

    class Meta:
        model = Airport
        fields = ["airportid", "name", "address", "city", "country", "zipcode"]

    def clean_airportid(self):
        return self.clean_identifier(self.cleaned_data["airportid"], minimum=3, maximum=4)


class AirplaneForm(UppercaseIdentifierModelForm):
    identifier_field = "airplaneid"

    class Meta:
        model = Airplane
        fields = ["airplaneid", "type", "numseats", "totalfuel"]
        widgets = {
            "numseats": forms.NumberInput(attrs={"min": 1, "max": 999}),
            "totalfuel": forms.NumberInput(attrs={"min": 0}),
        }

    def clean_airplaneid(self):
        return self.clean_identifier(
            self.cleaned_data["airplaneid"], minimum=1, maximum=8, letters_only=False
        )

    def clean_numseats(self):
        numseats = self.cleaned_data["numseats"]
        if not 1 <= numseats <= 999:
            raise forms.ValidationError("Ensure this value is between 1 and 999.")
        if self.instance.pk:
            flight = (
                self.instance.flights.annotate(sold=Count("tickets"))
                .filter(sold__gt=numseats)
                .order_by("-sold", "flightnum")
                .first()
            )
            if flight:
                raise forms.ValidationError(
                    f"{flight.sold} tickets are already sold on flight {flight.flightnum}."
                )
        return numseats
