import pytest

from accounts.services import AccountError, activate_account, deactivate_account
from tests.factories import EmployeeFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_activate_account():
    actor = UserFactory()
    employee = EmployeeFactory(with_user=True)
    employee.user.is_active = False
    employee.user.save(update_fields=["is_active"])

    assert activate_account(employee, actor) == f"Account {employee.pk} activated."
    employee.user.refresh_from_db()
    assert employee.user.is_active


def test_activate_employee_without_account_fails():
    with pytest.raises(AccountError, match="This employee has no account"):
        activate_account(EmployeeFactory(user=None), UserFactory())


def test_deactivate_account():
    actor = UserFactory()
    employee = EmployeeFactory(with_user=True)

    assert deactivate_account(employee, actor) == f"Account {employee.pk} deactivated."
    employee.user.refresh_from_db()
    assert not employee.user.is_active


def test_cannot_deactivate_own_account():
    employee = EmployeeFactory(with_user=True)

    with pytest.raises(AccountError, match="You cannot deactivate your own account"):
        deactivate_account(employee, employee.user)
    employee.user.refresh_from_db()
    assert employee.user.is_active
