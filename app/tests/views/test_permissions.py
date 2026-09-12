import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import get_resolver, reverse

from accounts.permissions import role_required
from accounts.roles import Role
from tests.factories import (
    AirplaneFactory,
    AirportFactory,
    BuyFactory,
    CrewFactory,
    DepartmentFactory,
    EmployeeFactory,
    FlightFactory,
    PassengerFactory,
    ShiftFactory,
    TicketFactory,
    UserFactory,
)

pytestmark = pytest.mark.django_db

ALL_ROLES = tuple(Role)
SALES = (Role.SALES,)
SALES_AND_CEO = (Role.SALES, Role.CEO)
SCHEDULE = (Role.SCHEDULE,)
IT = (Role.IT,)
IT_AND_SCHEDULE = (Role.IT, Role.SCHEDULE)
HR = (Role.HR,)
HR_AND_CEO = (Role.HR, Role.CEO)

ROLE_MATRIX: list[tuple[str, dict | None, tuple[Role, ...]]] = [
    ("accounts:password_change", None, ALL_ROLES),
    ("core:home", None, ALL_ROLES),
    ("it:users", None, IT),
    ("it:user_password_shown", None, IT),
    ("it:user_reset_password", {"empid": "12345678"}, IT),
    ("it:user_activate", {"empid": "12345678"}, IT),
    ("it:user_deactivate", {"empid": "12345678"}, IT),
    ("it:airports", None, IT_AND_SCHEDULE),
    ("it:airport_create", None, IT_AND_SCHEDULE),
    ("it:airport_edit", {"airportid": "R22"}, IT_AND_SCHEDULE),
    ("it:airport_delete", {"airportid": "R22"}, IT_AND_SCHEDULE),
    ("it:airplanes", None, IT_AND_SCHEDULE),
    ("it:airplane_create", None, IT_AND_SCHEDULE),
    ("it:airplane_edit", {"airplaneid": "R2200001"}, IT_AND_SCHEDULE),
    ("it:airplane_delete", {"airplaneid": "R2200001"}, IT_AND_SCHEDULE),
    ("hr:employees", None, HR_AND_CEO),
    ("hr:employee_create", None, HR),
    ("hr:employee_detail", {"empid": "12345678"}, HR_AND_CEO),
    ("hr:employee_edit", {"empid": "12345678"}, HR),
    ("hr:departments", None, HR),
    ("hr:department_edit", {"deptid": 5}, HR),
    ("schedule:crews", None, SCHEDULE),
    ("schedule:crew_create", None, SCHEDULE),
    ("schedule:crew_edit", {"crewid": 123}, SCHEDULE),
    ("schedule:crew_delete", {"crewid": 123}, SCHEDULE),
    ("schedule:shifts", None, SCHEDULE),
    ("schedule:shift_create", None, SCHEDULE),
    ("schedule:shift_edit", {"shiftid": 123}, SCHEDULE),
    ("schedule:shift_delete", {"shiftid": 123}, SCHEDULE),
    ("schedule:flights", None, SCHEDULE),
    ("schedule:flight_create", None, SCHEDULE),
    ("schedule:flights_generate", None, SCHEDULE),
    ("schedule:flight_edit", {"flightid": 123}, SCHEDULE),
    ("schedule:flight_delete", {"flightid": 123}, SCHEDULE),
    ("crew:my_shifts", None, (Role.CREW,)),
    ("ceo:dashboard", None, (Role.CEO,)),
    ("sales:sell_step1", None, SALES),
    ("sales:sell_step2", None, SALES),
    ("sales:passenger_name", None, SALES),
    ("sales:buy_detail", {"buyid": 123}, SALES_AND_CEO),
    ("sales:receipt", {"buyid": 123}, SALES_AND_CEO),
    ("sales:boarding_passes", {"buyid": 123}, SALES_AND_CEO),
    ("sales:passenger_list", None, SALES),
    ("sales:passenger_create", None, SALES),
    ("sales:passenger_detail", {"clientid": 123}, SALES),
    ("sales:passenger_edit", {"clientid": 123}, SALES),
    ("sales:flight_search", None, (Role.SALES, Role.CEO, Role.SCHEDULE, Role.CREW)),
    ("sales:ticket_search", None, SALES_AND_CEO),
    ("sales:boarding_pass", {"ticketid": "CB00000123"}, SALES_AND_CEO),
    ("sales:ticket_detail", {"ticketid": "CB00000123"}, SALES_AND_CEO),
]

POST_URLS = {
    "it:user_reset_password",
    "it:user_activate",
    "it:user_deactivate",
}
ALLOWED_REDIRECTS = {
    "it:user_reset_password",
    "it:user_activate",
    "it:user_deactivate",
    "sales:sell_step2",
}


@pytest.fixture
def permission_objects():
    department = DepartmentFactory(deptid=5)
    employee = EmployeeFactory(empid="12345678", dept=department, user=UserFactory())
    airport = AirportFactory(airportid="R22")
    airplane = AirplaneFactory(airplaneid="R2200001")
    crew_department = DepartmentFactory(deptid=2)
    crew = CrewFactory(
        crewid=123,
        commander__dept=crew_department,
        copilote__dept=crew_department,
        fachief__dept=crew_department,
        fliattendant1__dept=crew_department,
        fliattendant2__dept=crew_department,
        fliattendant3__dept=crew_department,
    )
    shift = ShiftFactory(shiftid=123, crew=crew)
    flight = FlightFactory(
        flightid=123,
        shift=shift,
        airplane=airplane,
        airportdep=airport,
    )
    passenger = PassengerFactory(clientid=123)
    buy = BuyFactory(buyid=123, client=passenger, emp=employee)
    TicketFactory(
        ticketid="CB00000123",
        buy=buy,
        client=passenger,
        flight=flight,
    )


def names_in_namespace(namespace):
    resolver = get_resolver().namespace_dict[namespace][1]
    return {f"{namespace}:{name}" for name in resolver.reverse_dict if isinstance(name, str)}


def test_role_matrix_covers_every_application_url():
    namespaces = ("accounts", "core", "it", "hr", "schedule", "crew", "ceo", "sales")
    routed_names = set().union(*(names_in_namespace(namespace) for namespace in namespaces))
    routed_names -= {"accounts:login", "accounts:logout", "core:healthz"}
    assert {url_name for url_name, _, _ in ROLE_MATRIX} == routed_names


@pytest.mark.parametrize(("url_name", "kwargs", "allowed_roles"), ROLE_MATRIX)
@pytest.mark.parametrize("role", ALL_ROLES)
def test_role_matrix(role_client, permission_objects, url_name, kwargs, allowed_roles, role):
    client = role_client(role)
    url = reverse(url_name, kwargs=kwargs)
    request = client.post if url_name in POST_URLS else client.get
    response = request(url)
    expected = 302 if role in allowed_roles and url_name in ALLOWED_REDIRECTS else 200
    if role in allowed_roles and url_name == "core:home" and role != Role.LEGAL:
        expected = 302
    if role not in allowed_roles:
        expected = 403
    assert response.status_code == expected


@pytest.mark.parametrize(("url_name", "kwargs", "allowed_roles"), ROLE_MATRIX)
def test_role_matrix_redirects_anonymous_users(
    client,
    permission_objects,
    url_name,
    kwargs,
    allowed_roles,
):
    url = reverse(url_name, kwargs=kwargs)
    request = client.post if url_name in POST_URLS else client.get
    response = request(url)
    assert response.status_code == 302
    assert response.url.startswith(f"/login/?next={url}")


@role_required(Role.SALES)
def sales_only(request):
    return HttpResponse("allowed")


def request_for(user):
    request = RequestFactory().get("/sales/")
    request.user = user
    return request


def test_anonymous_is_redirected():
    response = sales_only(request_for(AnonymousUser()))
    assert response.status_code == 302
    assert response.url == "/login/?next=/sales/"


def test_other_role_is_denied():
    employee = EmployeeFactory(dept=DepartmentFactory(deptid=6), with_user=True)
    with pytest.raises(PermissionDenied):
        sales_only(request_for(employee.user))


def test_allowed_role():
    employee = EmployeeFactory(dept=DepartmentFactory(deptid=7), with_user=True)
    assert sales_only(request_for(employee.user)).status_code == 200


def test_superuser_without_employee():
    user = UserFactory(is_superuser=True)
    assert sales_only(request_for(user)).status_code == 200
