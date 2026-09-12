from datetime import date, time
from decimal import Decimal

import pytest
from django.urls import reverse

from tests.factories import BuyFactory, DepartmentFactory, EmployeeFactory

pytestmark = pytest.mark.django_db


def login_role(client, deptid):
    employee = EmployeeFactory(dept=DepartmentFactory(deptid=deptid), with_user=True)
    client.force_login(employee.user)


def test_receipt_contains_sale_data_without_application_menu(client):
    login_role(client, 7)
    buy = BuyFactory(
        buyid=42,
        buydate=date(2026, 9, 11),
        buytime=time(14, 5, 6),
        price=Decimal("120.99") * 3,
    )

    response = client.get(reverse("sales:receipt", args=[buy.buyid]))

    assert response.status_code == 200
    body = response.content.decode()
    for text in (
        "RECEIPT",
        "BUYID: 42",
        "CB/CS/CH",
        "Payment: not recorded",
        "Le 11/09/2026 a 14:05:06",
        "MONTANT = 362.97 EUR",
        "DEBIT/CREDIT",
        "TICKET CLIENT",
        "TO KEEP",
    ):
        assert text in body
    assert "Logout" not in body


def test_missing_buy_returns_404(client):
    login_role(client, 7)
    assert client.get(reverse("sales:receipt", args=[999999])).status_code == 404
