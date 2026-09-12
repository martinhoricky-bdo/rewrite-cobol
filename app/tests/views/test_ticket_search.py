from html import escape

import pytest

from core.messages import E_TKT_01, E_TKT_02, E_TKT_03
from tests.factories import DepartmentFactory, EmployeeFactory, TicketFactory

pytestmark = pytest.mark.django_db


def login_role(client, deptid):
    employee = EmployeeFactory(dept=DepartmentFactory(deptid=deptid), with_user=True)
    client.force_login(employee.user)


def test_initial_page_does_not_validate(client):
    login_role(client, 7)
    response = client.get("/sales/tickets/")
    assert response.status_code == 200
    assert E_TKT_01 not in response.content.decode()


def test_invalid_search_and_empty_results_show_messages(client):
    login_role(client, 7)
    assert escape(E_TKT_01) in client.get("/sales/tickets/?flightnum=CB2204").content.decode()
    assert E_TKT_02 in client.get("/sales/tickets/?clientid=999999").content.decode()
    assert E_TKT_02 in client.get("/sales/tickets/?ticketid=XYZ").content.decode()


def test_results_are_paginated(client):
    login_role(client, 7)
    passenger = TicketFactory().client
    for _ in range(14):
        TicketFactory(client=passenger, buy__client=passenger)
    response = client.get(f"/sales/tickets/?clientid={passenger.clientid}")
    assert len(response.context["page_obj"]) == 10
    assert "page=2" in response.content.decode()


def test_detail_contains_ticket_and_purchase(client):
    login_role(client, 7)
    ticket = TicketFactory(
        ticketid="CB00000001",
        buy__client__firstname="MAXIME",
        buy__client__lastname="DUPRAT",
        seat="B04",
    )
    response = client.get(f"/sales/tickets/{ticket.ticketid}/")
    body = response.content.decode()
    assert response.status_code == 200
    for text in ("TICKET ID", "MAXIME", "DUPRAT", "SEAT", "B04", "Purchase", "BUYID"):
        assert text in body


def test_missing_ticket_uses_custom_404(client):
    login_role(client, 7)
    response = client.get("/sales/tickets/CB99999999/")
    assert response.status_code == 404
    assert E_TKT_03 in response.content.decode()
