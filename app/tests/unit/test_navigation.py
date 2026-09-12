import pytest

from accounts.roles import Role
from core.navigation import COMMON_MENU, MENU

EXPECTED_ROLE_MENU = {
    Role.SALES: {"Search flight", "Search ticket", "Passengers", "Sell"},
    Role.IT: {"Users", "Airports", "Airplanes"},
    Role.HR: {"Employees", "Departments"},
    Role.SCHEDULE: {
        "Search flight",
        "Flights",
        "Generate flights",
        "Crews",
        "Shifts",
        "Airports",
        "Airplanes",
    },
    Role.CREW: {"My shifts", "Search flight"},
    Role.CEO: {"Dashboard", "Search flight", "Search ticket", "Employees"},
    Role.LEGAL: set(),
}


@pytest.mark.parametrize(("role", "expected"), EXPECTED_ROLE_MENU.items())
def test_role_navigation_matches_permission_matrix(role, expected):
    assert {label for label, _ in MENU[role]} == expected
    assert {label for label, _ in COMMON_MENU} == {"Change password", "Logout"}
