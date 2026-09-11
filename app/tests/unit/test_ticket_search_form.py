from core.messages import E_FLT_02, E_TKT_01
from sales.forms import TicketSearchForm


def test_only_flight_number_is_not_a_valid_search():
    form = TicketSearchForm({"flightnum": "CB2204"})
    assert not form.is_valid()
    assert E_TKT_01 in form.non_field_errors()


def test_only_first_name_is_not_a_valid_search():
    form = TicketSearchForm({"firstname": "Maxime"})
    assert not form.is_valid()
    assert E_TKT_01 in form.non_field_errors()


def test_client_id_must_be_positive():
    form = TicketSearchForm({"clientid": "0"})
    assert not form.is_valid()
    assert "clientid" in form.errors


def test_date_uses_custom_error_message():
    form = TicketSearchForm({"clientid": "1", "flightdate": "01-09-2022"})
    assert not form.is_valid()
    assert E_FLT_02 in form.errors["flightdate"]


def test_valid_name_and_flight_combination_is_trimmed():
    form = TicketSearchForm(
        {"firstname": " Maxime ", "lastname": " Duprat ", "flightnum": " CB2204 "}
    )
    assert form.is_valid()
    assert form.cleaned_data["firstname"] == "Maxime"
    assert form.cleaned_data["flightnum"] == "CB2204"
