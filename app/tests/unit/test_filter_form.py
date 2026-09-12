import pytest
from django import forms
from django.core.exceptions import ImproperlyConfigured

from core.forms import FilterForm


class ExampleFilterForm(FilterForm):
    date = forms.DateField(required=False)
    query = forms.CharField(required=False)


def test_value_uses_valid_fields_when_another_field_is_invalid():
    form = ExampleFilterForm({"date": "not-a-date", "query": "CDG"})

    assert form.value("date", "fallback") == "fallback"
    assert form.value("query") == "CDG"


def test_required_filter_field_is_rejected():
    class InvalidFilterForm(FilterForm):
        query = forms.CharField(required=True)

    with pytest.raises(ImproperlyConfigured):
        InvalidFilterForm()
