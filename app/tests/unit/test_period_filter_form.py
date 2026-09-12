from datetime import date

from reports.forms import PeriodFilterForm


def test_period_filter_uses_defaults_for_invalid_and_empty_values():
    default_from = date(2026, 9, 1)
    default_to = date(2026, 9, 12)
    form = PeriodFilterForm({"from": "invalid", "to": ""})
    assert form.value("from", default_from) == default_from
    assert form.value("to", default_to) == default_to


def test_period_filter_accepts_valid_dates():
    form = PeriodFilterForm({"from": "2026-08-01", "to": "2026-08-31"})
    assert form.value("from") == date(2026, 8, 1)
    assert form.value("to") == date(2026, 8, 31)
