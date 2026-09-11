from datetime import date, time

import pytest
from django.urls import reverse

from core.messages import E_TKT_03
from tests.factories import DepartmentFactory, EmployeeFactory, TicketFactory

pytestmark = pytest.mark.django_db


def login_role(client, deptid):
    employee = EmployeeFactory(dept=DepartmentFactory(deptid=deptid), with_user=True)
    client.force_login(employee.user)


def reference_ticket():
    return TicketFactory(
        ticketid="CB00000001",
        seat="B04",
        buy__client__firstname="Maxime",
        buy__client__lastname="Duprat",
        flight__flightnum="CB2204",
        flight__flightdate=date(2022, 9, 1),
        flight__deptime=time(10),
        flight__airportdep__airportid="CDG",
        flight__airportdep__city="Roissy",
        flight__airportarr__airportid="FCO",
        flight__airportarr__city="Fiumicino",
    )


def test_boarding_pass_contains_reference_ticket_without_application_menu(client):
    login_role(client, 7)
    ticket = reference_ticket()
    response = client.get(reverse("sales:boarding_pass", args=[ticket.ticketid.lower()]))

    assert response.status_code == 200
    body = response.content.decode()
    for text in (
        "MAXIME DUPRAT",
        "B04",
        "CB2204",
        "ROISSY-CDG",
        "FIUMICINO-FCO",
        "01SEP2022",
        "2022-09-01",
        "10:00",
    ):
        assert text in body
    assert "Logout" not in body


def test_missing_ticket_uses_custom_404(client):
    login_role(client, 7)
    response = client.get(reverse("sales:boarding_pass", args=["CB99999999"]))
    assert response.status_code == 404
    assert E_TKT_03 in response.content.decode()


@pytest.mark.parametrize("deptid", [7, 1])
def test_authorized_roles_can_access(client, deptid):
    login_role(client, deptid)
    ticket = reference_ticket()
    assert client.get(reverse("sales:boarding_pass", args=[ticket.ticketid])).status_code == 200


def test_hr_role_is_denied(client):
    login_role(client, 5)
    ticket = reference_ticket()
    assert client.get(reverse("sales:boarding_pass", args=[ticket.ticketid])).status_code == 403


def test_anonymous_user_is_redirected(client):
    url = reverse("sales:boarding_pass", args=["CB00000001"])
    response = client.get(url)
    assert response.status_code == 302
    assert response.url == f"/login/?next={url}"


def test_ticket_detail_links_to_boarding_pass_in_new_tab(client):
    login_role(client, 7)
    ticket = reference_ticket()
    response = client.get(reverse("sales:ticket_detail", args=[ticket.ticketid]))
    expected_url = reverse("sales:boarding_pass", args=[ticket.ticketid])
    assert f'href="{expected_url}" target="_blank"' in response.content.decode()
