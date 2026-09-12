from accounts.permissions import current_role
from accounts.roles import Role

ROLE_HOME: dict[Role, str | None] = {role: None for role in Role}
MENU: dict[Role, list[tuple[str, str]]] = {role: [] for role in Role}
for role in (Role.SALES, Role.CEO, Role.SCHEDULE, Role.CREW):
    MENU[role].append(("Search flight", "sales:flight_search"))
for role in (Role.SALES, Role.CEO):
    MENU[role].append(("Search ticket", "sales:ticket_search"))
MENU[Role.SALES].append(("Passengers", "sales:passenger_list"))
MENU[Role.SALES].append(("Sell", "sales:sell_step1"))
ROLE_HOME[Role.SALES] = "sales:flight_search"
ROLE_HOME[Role.IT] = "it:users"
MENU[Role.IT] = [
    ("Users", "it:users"),
    ("Airports", "it:airports"),
    ("Airplanes", "it:airplanes"),
]
MENU[Role.SCHEDULE].extend([("Airports", "it:airports"), ("Airplanes", "it:airplanes")])
ROLE_HOME[Role.SCHEDULE] = "schedule:flights"
MENU[Role.SCHEDULE] = [
    ("Flights", "schedule:flights"),
    ("Generate flights", "schedule:flights_generate"),
    ("Crews", "schedule:crews"),
    ("Shifts", "schedule:shifts"),
    *MENU[Role.SCHEDULE],
]
ROLE_HOME[Role.HR] = "hr:employees"
MENU[Role.HR] = [("Employees", "hr:employees"), ("Departments", "hr:departments")]
MENU[Role.CEO].append(("Employees", "hr:employees"))
ROLE_HOME[Role.CREW] = "crew:my_shifts"
MENU[Role.CREW] = [
    ("My shifts", "crew:my_shifts"),
    ("Search flight", "sales:flight_search"),
]
ROLE_HOME[Role.CEO] = "ceo:dashboard"
MENU[Role.CEO] = [
    ("Dashboard", "ceo:dashboard"),
    ("Search flight", "sales:flight_search"),
    ("Search ticket", "sales:ticket_search"),
    ("Employees", "hr:employees"),
]
COMMON_MENU = [
    ("Change password", "accounts:password_change"),
    ("Logout", "accounts:logout"),
]


def menu_for(user) -> list[tuple[str, str]]:
    if not user.is_authenticated:
        return []
    role = current_role(user)
    return [*MENU.get(role, []), *COMMON_MENU]
