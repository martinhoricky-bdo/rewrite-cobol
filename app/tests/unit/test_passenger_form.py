import pytest

from sales.forms import TELEPHONE_ERROR, PassengerForm


def valid_data():
    return {
        "firstname": "Jean",
        "lastname": "Martin",
        "address": "1 Rue de Paris",
        "city": "Paris",
        "country": "France",
        "zipcode": "75001",
        "telephone": "+33 6 66 66 66 66",
        "email": "jean@example.com",
    }


@pytest.mark.parametrize("field", PassengerForm.Meta.fields)
def test_each_field_is_required(field):
    data = valid_data()
    data[field] = ""
    form = PassengerForm(data=data)
    assert not form.is_valid()
    assert field in form.errors


def test_firstname_max_length():
    form = PassengerForm(data={**valid_data(), "firstname": "x" * 31})
    assert not form.is_valid()
    assert "firstname" in form.errors


def test_email_must_be_valid():
    form = PassengerForm(data={**valid_data(), "email": "not-an-email"})
    assert not form.is_valid()
    assert "email" in form.errors


def test_telephone_rejects_letters():
    form = PassengerForm(data={**valid_data(), "telephone": "abc"})
    assert not form.is_valid()
    assert TELEPHONE_ERROR in form.errors["telephone"]


def test_telephone_accepts_supported_characters():
    assert PassengerForm(data=valid_data()).is_valid()


def test_values_are_trimmed():
    data = {key: f"  {value}  " for key, value in valid_data().items()}
    form = PassengerForm(data=data)
    assert form.is_valid(), form.errors
    assert form.cleaned_data == valid_data()
