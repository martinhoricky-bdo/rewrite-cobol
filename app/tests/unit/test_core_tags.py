import pytest

from core.templatetags.core_tags import account_status
from tests.factories import EmployeeFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_account_status_without_account():
    assert account_status(EmployeeFactory(user=None)) == "no account"


def test_account_status_inactive():
    assert account_status(EmployeeFactory(user=UserFactory(is_active=False))) == "inactive"


def test_account_status_without_usable_password():
    user = UserFactory()
    user.set_unusable_password()
    assert account_status(EmployeeFactory(user=user)) == "no password"


def test_account_status_active():
    assert account_status(EmployeeFactory(user=UserFactory())) == "active"
