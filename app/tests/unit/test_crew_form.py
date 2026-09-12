import pytest

from operations.forms import CrewForm
from tests.factories import DepartmentFactory, EmployeeFactory

pytestmark = pytest.mark.django_db


def employees():
    commander = EmployeeFactory(dept=DepartmentFactory(deptid=2))
    copilote = EmployeeFactory(dept=DepartmentFactory(deptid=3))
    attendants = [EmployeeFactory(dept=DepartmentFactory(deptid=4)) for _ in range(4)]
    return commander, copilote, attendants


def data_for(commander, copilote, attendants):
    return {
        "commander": commander.pk,
        "copilote": copilote.pk,
        "fachief": attendants[0].pk,
        "fliattendant1": attendants[1].pk,
        "fliattendant2": attendants[2].pk,
        "fliattendant3": attendants[3].pk,
    }


def test_member_from_wrong_department_is_not_a_valid_choice():
    commander, copilote, attendants = employees()
    form = CrewForm(data=data_for(copilote, copilote, attendants))
    assert not form.is_valid()
    assert "Select a valid choice" in form.errors["commander"][0]


def test_duplicate_member_is_rejected():
    commander, copilote, attendants = employees()
    values = data_for(commander, copilote, attendants)
    values["fliattendant3"] = attendants[0].pk
    form = CrewForm(data=values)
    assert not form.is_valid()
    assert "Crew members must be different employees." in form.non_field_errors()
