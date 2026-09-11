from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils import timezone

from accounts.permissions import role_required
from accounts.roles import Role
from core.messages import E_FLT_03
from operations.services import search_flights

from .forms import FlightSearchForm


@role_required(Role.SALES, Role.CEO, Role.SCHEDULE, Role.CREW)
def flight_search(request):
    form = FlightSearchForm(request.GET or None)
    page_obj = None
    if form.is_bound:
        if form.is_valid():
            flights = search_flights(**form.cleaned_data, today=timezone.localdate())
            paginator = Paginator(flights, 10)
            page_obj = paginator.get_page(request.GET.get("page"))
            if paginator.count == 0:
                messages.info(request, E_FLT_03)
        else:
            for errors in form.errors.values():
                for error in errors:
                    messages.error(request, error)

    query_params = request.GET.copy()
    query_params.pop("page", None)
    return render(
        request,
        "sales/flight_search.html",
        {"form": form, "page_obj": page_obj, "query_params": query_params.urlencode()},
    )
