import pytest

from accounts.roles import ROLE_BY_DEPT, Role
from tests.factories import DepartmentFactory, EmployeeFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("deptid,expected", list(ROLE_BY_DEPT.items()))
def test_employee_role_is_derived_from_department(deptid, expected):
    employee = EmployeeFactory(dept=DepartmentFactory(deptid=deptid))
    assert employee.role == expected


def test_role_mapping_covers_all_legacy_departments():
    assert ROLE_BY_DEPT == {
        1: Role.CEO,
        2: Role.CREW,
        3: Role.CREW,
        4: Role.CREW,
        5: Role.HR,
        6: Role.IT,
        7: Role.SALES,
        8: Role.LEGAL,
        9: Role.SCHEDULE,
    }


def test_employee_full_name():
    employee = EmployeeFactory(firstname="Jane", lastname="Doe")
    assert employee.full_name == "Jane Doe"
