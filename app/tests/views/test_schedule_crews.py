import pytest
from django.urls import reverse

from core.messages import E_REF_01
from operations.models import Crew
from tests.factories import (
    CrewFactory,
    DepartmentFactory,
    EmployeeFactory,
    ShiftFactory,
    UserFactory,
)

pytestmark = pytest.mark.django_db


def login_as(client, deptid=9):
    user = UserFactory()
    EmployeeFactory(user=user, dept=DepartmentFactory(deptid=deptid))
    client.force_login(user)


def crew_data():
    commander = EmployeeFactory(dept=DepartmentFactory(deptid=2))
    copilote = EmployeeFactory(dept=DepartmentFactory(deptid=3))
    attendants = [EmployeeFactory(dept=DepartmentFactory(deptid=4)) for _ in range(4)]
    return {
        "commander": commander.pk,
        "copilote": copilote.pk,
        "fachief": attendants[0].pk,
        "fliattendant1": attendants[1].pk,
        "fliattendant2": attendants[2].pk,
        "fliattendant3": attendants[3].pk,
    }


def test_crew_crud(client):
    login_as(client)
    response = client.get(reverse("schedule:crews"))
    assert response.status_code == 200
    response = client.post(reverse("schedule:crew_create"), crew_data())
    assert response.status_code == 302
    crew = Crew.objects.get()
    values = crew_data()
    response = client.post(reverse("schedule:crew_edit", args=[crew.pk]), values)
    assert response.status_code == 302
    crew.refresh_from_db()
    assert crew.commander_id == values["commander"]
    response = client.get(reverse("schedule:crew_delete", args=[crew.pk]))
    assert response.status_code == 200
    client.post(reverse("schedule:crew_delete", args=[crew.pk]))
    assert not Crew.objects.filter(pk=crew.pk).exists()


def test_crew_with_shifts_cannot_be_deleted(client):
    login_as(client)
    crew = CrewFactory()
    ShiftFactory(crew=crew)
    response = client.post(reverse("schedule:crew_delete", args=[crew.pk]), follow=True)
    assert E_REF_01.format(Entity="Crew", n=1, related="shifts") in response.content.decode()
    assert Crew.objects.filter(pk=crew.pk).exists()


@pytest.mark.parametrize(
    ("name", "args", "method"),
    [
        ("schedule:crews", [], "get"),
        ("schedule:crew_create", [], "get"),
        ("schedule:crew_create", [], "post"),
        ("schedule:crew_edit", [1], "get"),
        ("schedule:crew_edit", [1], "post"),
        ("schedule:crew_delete", [1], "get"),
        ("schedule:crew_delete", [1], "post"),
    ],
)
def test_sales_role_gets_403_for_every_crew_url(client, name, args, method):
    login_as(client, 7)
    assert getattr(client, method)(reverse(name, args=args)).status_code == 403
