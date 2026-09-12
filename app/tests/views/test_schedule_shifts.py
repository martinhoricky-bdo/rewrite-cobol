from datetime import date, time

import pytest
from django.urls import reverse

from accounts.roles import Role
from core.messages import E_REF_01
from operations.models import Shift
from tests.factories import (
    FlightFactory,
    ShiftFactory,
)

pytestmark = pytest.mark.django_db


def shift_data(shift, **updates):
    data = {
        "shiftdate": "2026-10-01",
        "begintime": "09:00",
        "endtime": "17:00",
        "crew": shift.crew_id,
    }
    data.update(updates)
    return data


def test_shift_filters_and_crud(role_client):
    client = role_client(Role.SCHEDULE)
    matching = ShiftFactory(shiftid=101, shiftdate=date(2026, 10, 1))
    other = ShiftFactory(shiftid=102, shiftdate=date(2026, 10, 2))
    response = client.get(
        reverse("schedule:shifts"),
        {"date_from": "2026-10-01", "date_to": "2026-10-02", "crew": matching.crew_id},
    )
    content = response.content.decode()
    assert str(matching.pk) in content
    assert f">{other.pk}<" not in content
    assert (
        client.get(reverse("schedule:shifts"), {"date_from": "bad", "crew": "bad"}).status_code
        == 200
    )
    response = client.post(
        reverse("schedule:shift_create"), shift_data(matching, begintime="18:00", endtime="20:00")
    )
    assert response.status_code == 302
    created = Shift.objects.exclude(pk__in=[matching.pk, other.pk]).get()
    response = client.post(
        reverse("schedule:shift_edit", args=[created.pk]),
        shift_data(created, begintime="20:00", endtime="22:00"),
    )
    assert response.status_code == 302
    assert client.get(reverse("schedule:shift_delete", args=[created.pk])).status_code == 200
    client.post(reverse("schedule:shift_delete", args=[created.pk]))
    assert not Shift.objects.filter(pk=created.pk).exists()


def test_shift_with_flights_cannot_be_deleted(role_client):
    client = role_client(Role.SCHEDULE)
    shift = ShiftFactory()
    FlightFactory(shift=shift)
    response = client.post(reverse("schedule:shift_delete", args=[shift.pk]), follow=True)
    assert E_REF_01.format(Entity="Shift", n=1, related="flights") in response.content.decode()
    assert Shift.objects.filter(pk=shift.pk).exists()


@pytest.mark.parametrize(
    ("begin", "end", "message"),
    [
        ("17:00", "09:00", "Begin time must be before end time."),
        ("11:00", "15:00", None),
    ],
)
def test_invalid_shift_create_reports_error_without_writing(role_client, begin, end, message):
    client = role_client(Role.SCHEDULE)
    existing = ShiftFactory(shiftdate=date(2026, 10, 1), begintime=time(8), endtime=time(12))
    before = Shift.objects.count()
    expected = message or (
        f"Crew {existing.crew_id} already has a shift on 2026-10-01 overlapping this time."
    )

    response = client.post(
        reverse("schedule:shift_create"), shift_data(existing, begintime=begin, endtime=end)
    )

    assert response.status_code == 200
    assert expected in response.content.decode()
    assert Shift.objects.count() == before
