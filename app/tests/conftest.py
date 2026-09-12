import pytest

from accounts.roles import ROLE_BY_DEPT
from tests.factories import DepartmentFactory, EmployeeFactory, UserFactory


@pytest.fixture
def employee_of():
    def factory(role):
        deptid = next(deptid for deptid, mapped_role in ROLE_BY_DEPT.items() if mapped_role == role)
        return EmployeeFactory(user=UserFactory(), dept=DepartmentFactory(deptid=deptid))

    return factory


@pytest.fixture
def role_client(client, employee_of):
    def factory(role):
        client.force_login(employee_of(role).user)
        return client

    return factory
