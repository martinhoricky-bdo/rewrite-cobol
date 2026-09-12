"""Design: forms for AIRPORT and AIRPLANE maintenance in UC-I02 and UC-I03, absent from
legacy screens.
"""

import re

from django import forms
from django.db.models import Count

from .models import Airplane, Airport


class UppercaseIdentifierModelForm(forms.ModelForm):
    """Provide UppercaseIdentifierModelForm behavior for the AIRPORT and AIRPLANE tables
    and Design use cases UC-I02/UC-I03.
    """

    identifier_field = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields[self.identifier_field].disabled = True

    def clean_identifier(
        self, value: str, *, minimum: int, maximum: int, letters_only: bool = True
    ) -> str:
        """Implement clean_identifier behavior for the AIRPORT and AIRPLANE tables and
        Design use cases UC-I02/UC-I03.
        """
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
    """Provide AirportForm behavior for the AIRPORT and AIRPLANE tables and Design use
    cases UC-I02/UC-I03.
    """

    identifier_field = "airportid"

    class Meta:
        """Provide Meta behavior for the AIRPORT and AIRPLANE tables and Design use cases
        UC-I02/UC-I03.
        """

        model = Airport
        fields = ["airportid", "name", "address", "city", "country", "zipcode"]

    def clean_airportid(self):
        """Implement clean_airportid behavior for the AIRPORT and AIRPLANE tables and
        Design use cases UC-I02/UC-I03.
        """
        return self.clean_identifier(self.cleaned_data["airportid"], minimum=3, maximum=4)


class AirplaneForm(UppercaseIdentifierModelForm):
    """Provide AirplaneForm behavior for the AIRPORT and AIRPLANE tables and Design use
    cases UC-I02/UC-I03.
    """

    identifier_field = "airplaneid"

    class Meta:
        """Provide Meta behavior for the AIRPORT and AIRPLANE tables and Design use cases
        UC-I02/UC-I03.
        """

        model = Airplane
        fields = ["airplaneid", "type", "numseats", "totalfuel"]
        widgets = {
            "numseats": forms.NumberInput(attrs={"min": 1, "max": 999}),
            "totalfuel": forms.NumberInput(attrs={"min": 0}),
        }

    def clean_airplaneid(self):
        """Implement clean_airplaneid behavior for the AIRPORT and AIRPLANE tables and
        Design use cases UC-I02/UC-I03.
        """
        return self.clean_identifier(
            self.cleaned_data["airplaneid"], minimum=1, maximum=8, letters_only=False
        )

    def clean_numseats(self):
        """Implement clean_numseats behavior for the AIRPORT and AIRPLANE tables and Design
        use cases UC-I02/UC-I03.
        """
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
