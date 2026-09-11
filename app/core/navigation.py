from accounts.permissions import current_role
from accounts.roles import Role

ROLE_HOME: dict[Role, str | None] = {role: None for role in Role}
MENU: dict[Role, list[tuple[str, str]]] = {role: [] for role in Role}
for role in (Role.SALES, Role.CEO, Role.SCHEDULE, Role.CREW):
    MENU[role].append(("Search flight", "sales:flight_search"))
for role in (Role.SALES, Role.CEO):
    MENU[role].append(("Search ticket", "sales:ticket_search"))
ROLE_HOME[Role.SALES] = "sales:flight_search"
COMMON_MENU = [
    ("Change password", "accounts:password_change"),
    ("Logout", "accounts:logout"),
]


def menu_for(user) -> list[tuple[str, str]]:
    if not user.is_authenticated:
        return []
    role = current_role(user)
    return [*MENU.get(role, []), *COMMON_MENU]
