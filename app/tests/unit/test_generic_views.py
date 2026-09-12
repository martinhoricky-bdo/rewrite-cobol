import pytest
from django import forms
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from django.urls import reverse

from accounts.roles import Role
from core.forms import FilterForm
from core.views.generic import FilteredListView, SearchListView
from fleet.models import Airport
from tests.factories import FlightFactory, UserFactory

pytestmark = pytest.mark.django_db


class AirportFilterForm(FilterForm):
    query = forms.CharField(required=False)


class AirportFilterView(FilteredListView):
    model = Airport
    filter_form_class = AirportFilterForm
    paginate_by = 1

    def filter_queryset(self, queryset, form):
        query = form.value("query")
        return queryset.filter(name__icontains=query) if query else queryset


class AirportSearchForm(FilterForm):
    number = forms.IntegerField(required=False)


class AirportSearchView(SearchListView):
    model = Airport
    filter_form_class = AirportSearchForm
    paginate_by = 1
    empty_message = "Nothing matched."

    def search_queryset(self, form):
        return Airport.objects.filter(pk=str(form.value("number")))


def airport(identifier, name):
    return Airport.objects.create(
        airportid=identifier,
        name=name,
        address="Road",
        city="City",
        country="Country",
        zipcode="1",
    )


def request(path):
    result = RequestFactory().get(path)
    result.session = {}
    result._messages = FallbackStorage(result)
    return result


def message_texts(result):
    return [str(message) for message in get_messages(result)]


def test_filtered_list_calls_filter_hook():
    airport("CDG", "Charles de Gaulle")
    airport("ORY", "Orly")

    response = AirportFilterView.as_view()(request("/?query=Charles"))

    assert list(response.context_data["object_list"].values_list("pk", flat=True)) == ["CDG"]


@pytest.mark.parametrize(("page", "expected"), [("abc", 1), ("999", 2)])
def test_filtered_list_uses_first_or_last_page(page, expected):
    airport("CDG", "Charles")
    airport("ORY", "Orly")

    response = AirportFilterView.as_view()(request(f"/?page={page}"))

    assert response.context_data["page_obj"].number == expected


def test_filtered_list_allows_no_filter_form():
    class UnfilteredAirportView(FilteredListView):
        model = Airport

    response = UnfilteredAirportView.as_view()(request("/"))

    assert response.context_data["form"] is None


def test_unbound_search_has_no_results_or_page():
    result = request("/")

    response = AirportSearchView.as_view()(result)

    assert not response.context_data["object_list"].exists()
    assert response.context_data["page_obj"] is None
    assert response.context_data["is_paginated"] is False


def test_invalid_search_adds_errors_to_messages():
    result = request("/?number=invalid")

    AirportSearchView.as_view()(result)

    assert "Enter a whole number." in message_texts(result)


def test_empty_search_adds_info_message():
    result = request("/?number=999")

    AirportSearchView.as_view()(result)

    assert message_texts(result) == ["Nothing matched."]


def test_saved_message_mixin_reports_created_object(role_client):
    client = role_client(Role.IT)
    response = client.post(
        reverse("it:airport_create"),
        {
            "airportid": "TST",
            "name": "Test",
            "address": "Road",
            "city": "City",
            "country": "Country",
            "zipcode": "1",
        },
        follow=True,
    )

    assert "Airport TST saved." in response.content.decode()


def test_protected_delete_reports_unique_references(role_client):
    client = role_client(Role.IT)
    flight = FlightFactory()

    response = client.post(reverse("it:airport_delete", args=[flight.airportdep_id]), follow=True)

    assert "Airport is used by 1 flights." in response.content.decode()


def test_successful_protected_delete_view_reports_success(role_client):
    client = role_client(Role.IT)
    item = airport("TST", "Test")

    response = client.post(reverse("it:airport_delete", args=[item.pk]), follow=True)

    assert "Airport TST deleted." in response.content.decode()


def test_role_required_mixin_redirects_anonymous(client):
    assert client.get(reverse("it:airports")).status_code == 302


def test_role_required_mixin_rejects_other_role(role_client):
    assert role_client(Role.HR).get(reverse("it:airports")).status_code == 403


def test_role_required_mixin_allows_superuser(client):
    client.force_login(UserFactory(is_superuser=True))
    assert client.get(reverse("it:airports")).status_code == 200
