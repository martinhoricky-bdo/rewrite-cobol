from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.permissions import role_required
from accounts.roles import Role

from .forms import AirplaneForm, AirportForm
from .models import Airplane, Airport
from .services import delete_airplane, delete_airport

FLEET_ROLES = (Role.IT, Role.SCHEDULE)


@role_required(*FLEET_ROLES)
def airports(request):
    return render(request, "it/airport_list.html", {"airports": Airport.objects.all()})


def _edit(request, *, instance, form_class, template, success_name, label):
    form = form_class(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        saved = form.save()
        messages.success(request, f"{label} {saved.pk} saved.")
        return redirect(success_name)
    return render(request, template, {"form": form, "object": instance})


@role_required(*FLEET_ROLES)
def airport_create(request):
    return _edit(
        request,
        instance=Airport(),
        form_class=AirportForm,
        template="it/fleet_form.html",
        success_name="it:airports",
        label="Airport",
    )


@role_required(*FLEET_ROLES)
def airport_edit(request, airportid):
    return _edit(
        request,
        instance=get_object_or_404(Airport, pk=airportid),
        form_class=AirportForm,
        template="it/fleet_form.html",
        success_name="it:airports",
        label="Airport",
    )


@role_required(*FLEET_ROLES)
def airport_delete(request, airportid):
    airport = get_object_or_404(Airport, pk=airportid)
    if request.method == "POST":
        error = delete_airport(airport)
        if error:
            messages.error(request, error)
        else:
            messages.success(request, f"Airport {airportid} deleted.")
        return redirect("it:airports")
    return render(request, "it/fleet_confirm_delete.html", {"object": airport, "kind": "airport"})


@role_required(*FLEET_ROLES)
def airplanes(request):
    return render(
        request, "it/airplane_list.html", {"airplanes": Airplane.objects.order_by("airplaneid")}
    )


@role_required(*FLEET_ROLES)
def airplane_create(request):
    return _edit(
        request,
        instance=Airplane(),
        form_class=AirplaneForm,
        template="it/fleet_form.html",
        success_name="it:airplanes",
        label="Airplane",
    )


@role_required(*FLEET_ROLES)
def airplane_edit(request, airplaneid):
    return _edit(
        request,
        instance=get_object_or_404(Airplane, pk=airplaneid),
        form_class=AirplaneForm,
        template="it/fleet_form.html",
        success_name="it:airplanes",
        label="Airplane",
    )


@role_required(*FLEET_ROLES)
def airplane_delete(request, airplaneid):
    airplane = get_object_or_404(Airplane, pk=airplaneid)
    if request.method == "POST":
        error = delete_airplane(airplane)
        if error:
            messages.error(request, error)
        else:
            messages.success(request, f"Airplane {airplaneid} deleted.")
        return redirect("it:airplanes")
    return render(request, "it/fleet_confirm_delete.html", {"object": airplane, "kind": "airplane"})
