import pytest

from core.messages import E_SEL_01, E_SEL_02, E_SEL_03, E_SEL_04
from sales.forms import SellStep1Form


@pytest.mark.parametrize(
    ("data", "field", "message"),
    [
        ({"flightnum": "CB1104", "flightdate": "2026-09-11", "count": 1}, "clientid", E_SEL_01),
        ({"clientid": 1, "flightdate": "2026-09-11", "count": 1}, "flightnum", E_SEL_02),
        ({"clientid": 1, "flightnum": "CB1104", "count": 1}, "flightdate", E_SEL_03),
        ({"clientid": 1, "flightnum": "CB1104", "flightdate": "2026-09-11"}, "count", E_SEL_04),
        (
            {"clientid": "abc", "flightnum": "CB1104", "flightdate": "2026-09-11", "count": 1},
            "clientid",
            E_SEL_01,
        ),
        (
            {"clientid": 1, "flightnum": "CB1104", "flightdate": "2026-09-11", "count": 0},
            "count",
            E_SEL_04,
        ),
        (
            {"clientid": 1, "flightnum": "CB1104", "flightdate": "2026-09-11", "count": 10},
            "count",
            E_SEL_04,
        ),
    ],
)
def test_field_errors_are_sale_messages(data, field, message):
    form = SellStep1Form(data)
    assert not form.is_valid()
    assert form.errors[field] == [message]
