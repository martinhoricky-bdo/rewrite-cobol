from datetime import date

from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils import timezone

from accounts.permissions import role_required
from accounts.roles import Role

from .services import crew_shifts, dashboard_report


def _iso_date(value: str | None, default: date) -> date:
    try:
        return date.fromisoformat(value or "")
    except ValueError:
        return default


@role_required(Role.CREW)
def my_shifts(request):
    today = timezone.localdate()
    include_past = request.GET.get("past") == "1"
    shifts = crew_shifts(request.user.employee, today=today, include_past=include_past)
    page_obj = Paginator(shifts, 20).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(
        request,
        "reports/my_shifts.html",
        {"page_obj": page_obj, "include_past": include_past, "query_params": params.urlencode()},
    )


@role_required(Role.CEO)
def dashboard(request):
    today = timezone.localdate()
    default_from = today.replace(day=1)
    date_from = _iso_date(request.GET.get("from"), default_from)
    date_to = _iso_date(request.GET.get("to"), today)
    if date_from > date_to:
        date_from, date_to = default_from, today
    return render(
        request,
        "reports/dashboard.html",
        {"date_from": date_from, "date_to": date_to, **dashboard_report(date_from, date_to)},
    )
