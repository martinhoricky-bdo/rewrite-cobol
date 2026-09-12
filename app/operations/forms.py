"""Design: schedule forms for UC-P01, UC-P03, and UC-P04 plus CBFLIGHT generation under
UC-P02.
"""

from datetime import timedelta
from decimal import Decimal

from django import forms

from accounts.models import Employee
from core.forms import FilterForm

from .models import Crew, Flight, Shift


class FlightFilterForm(FilterForm):
    """Validates and normalizes flight filter input for Design scheduling workflows in
    UC-P01–P04, using the field-specific messages declared below.
    """

    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    flightnum = forms.CharField(required=False, label="Flight number")
    airport = forms.CharField(required=False)


class ShiftFilterForm(FilterForm):
    """Validates and normalizes shift filter input for Design scheduling workflows in
    UC-P01–P04, using the field-specific messages declared below.
    """

    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    crew = forms.ModelChoiceField(
        required=False, queryset=Crew.objects.order_by("crewid"), empty_label="All"
    )


class EmployeeChoiceField(forms.ModelChoiceField):
    """Validates and normalizes employee input for Design scheduling workflows in UC-P01–P04,
    using the field-specific messages declared below.
    """

    def label_from_instance(self, employee: Employee) -> str:
        """Render a choice label containing the operational identifiers users need to distinguish
        records for employee choice field.
        """
        return f"{employee.pk} – {employee.full_name}"


class CrewForm(forms.ModelForm):
    """Validates and normalizes crew input for Design scheduling workflows in UC-P01–P04, using
    the field-specific messages declared below.
    """

    commander = EmployeeChoiceField(queryset=Employee.objects.none())
    copilote = EmployeeChoiceField(queryset=Employee.objects.none())
    fachief = EmployeeChoiceField(queryset=Employee.objects.none())
    fliattendant1 = EmployeeChoiceField(queryset=Employee.objects.none())
    fliattendant2 = EmployeeChoiceField(queryset=Employee.objects.none())
    fliattendant3 = EmployeeChoiceField(queryset=Employee.objects.none())

    class Meta:
        model = Crew
        fields = [
            "commander",
            "copilote",
            "fachief",
            "fliattendant1",
            "fliattendant2",
            "fliattendant3",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commander"].queryset = Employee.objects.filter(dept_id=2)
        self.fields["copilote"].queryset = Employee.objects.filter(dept_id=3)
        attendants = Employee.objects.filter(dept_id=4)
        for field in ("fachief", "fliattendant1", "fliattendant2", "fliattendant3"):
            self.fields[field].queryset = attendants

    def clean(self):
        """Validate related fields together and attach the applicable domain error messages for
        crew form.
        """
        cleaned = super().clean()
        members = [cleaned.get(field) for field in self._meta.fields]
        members = [member for member in members if member is not None]
        if len(members) != len(set(members)):
            raise forms.ValidationError("Crew members must be different employees.")
        return cleaned


class ShiftForm(forms.ModelForm):
    """Validates and normalizes shift input for Design scheduling workflows in UC-P01–P04,
    using the field-specific messages declared below.
    """

    class Meta:
        model = Shift
        fields = ["shiftdate", "begintime", "endtime", "crew"]
        widgets = {
            "shiftdate": forms.DateInput(attrs={"type": "date"}),
            "begintime": forms.TimeInput(attrs={"type": "time"}),
            "endtime": forms.TimeInput(attrs={"type": "time"}),
        }

    def clean(self):
        """Validate related fields together and attach the applicable domain error messages for
        shift form.
        """
        cleaned = super().clean()
        day = cleaned.get("shiftdate")
        begin = cleaned.get("begintime")
        end = cleaned.get("endtime")
        crew = cleaned.get("crew")
        if begin and end and begin >= end:
            raise forms.ValidationError("Begin time must be before end time.")
        if day and begin and end and crew and begin < end:
            overlaps = Shift.objects.filter(
                shiftdate=day, crew=crew, begintime__lt=end, endtime__gt=begin
            )
            if self.instance.pk:
                overlaps = overlaps.exclude(pk=self.instance.pk)
            if overlaps.exists():
                raise forms.ValidationError(
                    f"Crew {crew.pk} already has a shift on {day} overlapping this time."
                )
        return cleaned


class ShiftChoiceField(forms.ModelChoiceField):
    """Labels shift choices with date, crew, and period for clear scheduling."""

    def label_from_instance(self, shift: Shift) -> str:
        """Render a choice label containing the operational identifiers users need to distinguish
        records for shift choice field.
        """
        return (
            f"{shift.shiftdate} {shift.begintime:%H:%M}–{shift.endtime:%H:%M} crew {shift.crew_id}"
        )


class FlightForm(forms.ModelForm):
    """Validates and normalizes flight input for Design scheduling workflows in UC-P01–P04,
    using the field-specific messages declared below.
    """

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
        """Normalize the flight number and reject values that violate its required format."""
        return self.cleaned_data["flightnum"].strip().upper()

    def clean_price(self) -> Decimal:
        """Reject a non-positive fare with the flight form’s validation message."""
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("Price must be greater than zero.")
        return price

    def clean(self):
        """Validate related fields together and attach the applicable domain error messages for
        flight form.
        """
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
        """Persist the form record together with its normalized many-to-many assignments."""
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
    """Validates and normalizes flight generate input for Design scheduling workflows in
    UC-P01–P04, using the field-specific messages declared below.
    """

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
        """Validate related fields together and attach the applicable domain error messages for
        flight generate form.
        """
        cleaned = super().clean()
        start, end = cleaned.get("date_from"), cleaned.get("date_to")
        if start and end:
            if end < start:
                self.add_error("date_to", "End date must not be before start date.")
            elif end - start > timedelta(days=91):
                self.add_error("date_to", "The period must not exceed 92 days.")
        return cleaned

    def selected_weekdays(self) -> set[int]:
        """Return weekday numbers selected for recurring CBFLIGHT generation."""
        return {int(day) for day in self.cleaned_data["weekdays"]}
