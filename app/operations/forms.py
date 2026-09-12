from datetime import timedelta
from decimal import Decimal

from django import forms

from .models import Flight, Shift


class ShiftChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, shift: Shift) -> str:
        return (
            f"{shift.shiftdate} {shift.begintime:%H:%M}–{shift.endtime:%H:%M} crew {shift.crew_id}"
        )


class FlightForm(forms.ModelForm):
    shift = ShiftChoiceField(queryset=Shift.objects.none())

    class Meta:
        model = Flight
        fields = [
            "flightnum",
            "flightdate",
            "deptime",
            "arrtime",
            "airplane",
            "airportdep",
            "airportarr",
            "shift",
            "price",
        ]
        widgets = {
            "flightdate": forms.DateInput(attrs={"type": "date"}),
            "deptime": forms.TimeInput(attrs={"type": "time"}),
            "arrtime": forms.TimeInput(attrs={"type": "time"}),
            "price": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["shift"].queryset = Shift.objects.select_related("crew").order_by(
            "shiftdate", "begintime", "shiftid"
        )
        self.fields["price"].initial = Decimal("120.99")
        self._old_airplane_id = self.instance.airplane_id if self.instance.pk else None

    def clean_flightnum(self) -> str:
        return self.cleaned_data["flightnum"].strip().upper()

    def clean_price(self) -> Decimal:
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("Price must be greater than zero.")
        return price

    def clean(self):
        cleaned = super().clean()
        dep, arr = cleaned.get("airportdep"), cleaned.get("airportarr")
        if dep and arr and dep == arr:
            raise forms.ValidationError("Departure and arrival airports must differ.")
        number, day = cleaned.get("flightnum"), cleaned.get("flightdate")
        if number and day:
            duplicate = Flight.objects.filter(flightnum=number, flightdate=day)
            if self.instance.pk:
                duplicate = duplicate.exclude(pk=self.instance.pk)
            if duplicate.exists():
                raise forms.ValidationError(f"Flight {number} on {day} already exists.")
        return cleaned

    def save(self, commit=True):
        flight = super().save(commit=False)
        if not flight.pk or flight.airplane_id != self._old_airplane_id:
            flight.totpass = flight.airplane.numseats
        if not flight.pk:
            flight.totbagga = 0
        if commit:
            flight.save()
            self.save_m2m()
        return flight


class FlightGenerateForm(forms.Form):
    WEEKDAYS = tuple(
        (index, name)
        for index, name in enumerate(("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"))
    )

    template = forms.ModelChoiceField(queryset=Flight.objects.none())
    date_from = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    weekdays = forms.MultipleChoiceField(
        choices=WEEKDAYS,
        widget=forms.CheckboxSelectMultiple,
        initial=[str(index) for index in range(7)],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["template"].queryset = Flight.objects.select_related(
            "airportdep", "airportarr"
        ).order_by("flightdate", "flightnum")
        self.fields["template"].label_from_instance = lambda flight: (
            f"{flight.flightnum} {flight.flightdate} {flight.airportdep_id}→{flight.airportarr_id}"
        )

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("date_from"), cleaned.get("date_to")
        if start and end:
            if end < start:
                self.add_error("date_to", "End date must not be before start date.")
            elif end - start > timedelta(days=91):
                self.add_error("date_to", "The period must not exceed 92 days.")
        return cleaned

    def selected_weekdays(self) -> set[int]:
        return {int(day) for day in self.cleaned_data["weekdays"]}
