from datetime import date
from decimal import Decimal

import pytest
from freezegun import freeze_time

from tests.factories import BuyFactory, DepartmentFactory, EmployeeFactory

pytestmark = pytest.mark.django_db


def _employee(deptid):
    return EmployeeFactory(dept=DepartmentFactory(deptid=deptid), with_user=True)


@freeze_time("2026-09-12")
def test_ceo_dashboard_shows_cards_and_applies_period_filter(client):
    ceo = _employee(1)
    BuyFactory(buydate=date(2026, 9, 10), price=Decimal("120.99"))
    BuyFactory(buydate=date(2026, 8, 10), price=Decimal("999.00"))
    client.force_login(ceo.user)

    response = client.get("/ceo/dashboard/?from=2026-09-01&to=2026-09-12")

    assert response.status_code == 200
    content = response.content.decode()
    for label in ("Sales", "Revenue", "Tickets", "Average load factor", "Flights"):
        assert label in content
    assert "120.99 EUR" in content
    assert "999.00 EUR" not in content


@pytest.mark.parametrize(
    "query", ["?from=nonsense&to=2026-09-12", "?from=2026-09-01&to=invalid", "?from=9&to=1"]
)
@freeze_time("2026-09-12")
def test_ceo_dashboard_handles_invalid_filters(client, query):
    ceo = _employee(1)
    client.force_login(ceo.user)
    assert client.get(f"/ceo/dashboard/{query}").status_code == 200


def test_ceo_dashboard_forbids_foreign_role(client):
    crew = _employee(2)
    client.force_login(crew.user)
    assert client.get("/ceo/dashboard/").status_code == 403
