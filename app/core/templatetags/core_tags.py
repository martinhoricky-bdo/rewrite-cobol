from django import template

register = template.Library()


@register.simple_tag
def account_status(employee) -> str:
    """Return the display status of an employee's user account."""
    if not employee.user:
        return "no account"
    if not employee.user.is_active:
        return "inactive"
    if not employee.user.has_usable_password():
        return "no password"
    return "active"
