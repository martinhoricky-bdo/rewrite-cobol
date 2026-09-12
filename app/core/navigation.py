"""Role-aware navigation maps the reconstructed use cases to each legacy department menu."""

from typing import NamedTuple

from accounts.permissions import current_role
from accounts.roles import Role


class MenuItem(NamedTuple):
    """Provide MenuItem behavior for the shared CICS-inspired application design."""

    label: str
    url_name: str


ROLE_HOME: dict[Role, str | None] = {
    Role.SALES: "sales:flight_search",
    Role.IT: "it:users",
    Role.HR: "hr:employees",
    Role.SCHEDULE: "schedule:flights",
    Role.CREW: "crew:my_shifts",
    Role.CEO: "ceo:dashboard",
    Role.LEGAL: None,
}
MENU: dict[Role, tuple[MenuItem, ...]] = {
    Role.SALES: (
        MenuItem("Search flight", "sales:flight_search"),
        MenuItem("Search ticket", "sales:ticket_search"),
        MenuItem("Passengers", "sales:passenger_list"),
        MenuItem("Sell", "sales:sell_step1"),
    ),
    Role.IT: (
        MenuItem("Users", "it:users"),
        MenuItem("Airports", "it:airports"),
        MenuItem("Airplanes", "it:airplanes"),
    ),
    Role.HR: (MenuItem("Employees", "hr:employees"), MenuItem("Departments", "hr:departments")),
    Role.SCHEDULE: (
        MenuItem("Flights", "schedule:flights"),
        MenuItem("Generate flights", "schedule:flights_generate"),
        MenuItem("Crews", "schedule:crews"),
        MenuItem("Shifts", "schedule:shifts"),
        MenuItem("Search flight", "sales:flight_search"),
        MenuItem("Airports", "it:airports"),
        MenuItem("Airplanes", "it:airplanes"),
    ),
    Role.CREW: (
        MenuItem("My shifts", "crew:my_shifts"),
        MenuItem("Search flight", "sales:flight_search"),
    ),
    Role.CEO: (
        MenuItem("Dashboard", "ceo:dashboard"),
        MenuItem("Search flight", "sales:flight_search"),
        MenuItem("Search ticket", "sales:ticket_search"),
        MenuItem("Employees", "hr:employees"),
    ),
    Role.LEGAL: (),
}
COMMON_MENU = (
    MenuItem("Change password", "accounts:password_change"),
    MenuItem("Logout", "accounts:logout"),
)


def menu_for(user) -> list[MenuItem]:
    """Implement menu_for behavior for the shared CICS-inspired application design."""
    if not user.is_authenticated:
        return []
    return [*MENU.get(current_role(user), ()), *COMMON_MENU]
