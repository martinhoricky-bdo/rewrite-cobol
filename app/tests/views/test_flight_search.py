from datetime import date, timedelta

import pytest
from freezegun import freeze_time

from accounts.roles import Role
from core.messages import E_FLT_01, E_FLT_02, E_FLT_03
from tests.factories import DepartmentFactory, EmployeeFactory, FlightFactory

pytestmark = pytest.mark.django_db


def login_role(client, deptid):
    employee = EmployeeFactory(dept=DepartmentFactory(deptid=deptid), with_user=True)
    client.force_login(employee.user)


def test_initial_display_has_no_error(client):
    login_role(client, 7)
    response = client.get("/sales/flights/")
    assert response.status_code == 200
    assert E_FLT_01 not in response.content.decode()


def test_submitted_empty_form_shows_required_search_message(client):
    login_role(client, 7)
    response = client.get("/sales/flights/?flightnum=&flightdate=")
    assert E_FLT_01 in response.content.decode()
    assert response.context["page_obj"] is None


def test_bad_date_shows_custom_message(client):
    login_role(client, 7)
    response = client.get("/sales/flights/?flightdate=11-09-2026")
    assert E_FLT_02 in response.content.decode()
    assert response.context["page_obj"] is None


def test_invalid_date_reports_message_and_empty_result_list(role_client):
    client = role_client(Role.SALES)
    FlightFactory()

    response = client.get("/sales/flights/?flightdate=bad")

    assert E_FLT_02 in [str(message) for message in response.context["messages"]]
    assert list(response.context["object_list"]) == []


@freeze_time("2026-09-11")
def test_no_results_shows_message(client):
    login_role(client, 7)
    response = client.get("/sales/flights/?flightnum=CB9999")
    assert E_FLT_03 in response.content.decode()


@freeze_time("2026-09-11")
def test_results_are_paginated_and_query_is_preserved(client):
    login_role(client, 7)
    for offset in range(25):
        FlightFactory(flightnum="CB1104", flightdate=date(2026, 9, 11) + timedelta(days=offset))
    first = client.get("/sales/flights/?flightnum=CB1104")
    third = client.get("/sales/flights/?flightnum=CB1104&page=3")
    assert len(first.context["page_obj"]) == 10
    assert len(third.context["page_obj"]) == 5
    assert "flightnum=CB1104&amp;page=2" in first.content.decode()


def test_sales_home_redirects_to_flight_search(client):
    login_role(client, 7)
    response = client.get("/")
    assert response.status_code == 302
    assert response.url == "/sales/flights/"
