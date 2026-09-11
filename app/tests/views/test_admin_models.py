import pytest
from django.urls import reverse

from accounts.models import User

pytestmark = pytest.mark.django_db


def test_admin_index_lists_all_domain_models(client):
    user = User.objects.create_superuser("admin", "admin@example.com", "password")
    client.force_login(user)

    response = client.get(reverse("admin:index"))

    assert response.status_code == 200
    content = response.content.decode()
    for model_name in (
        "Departments",
        "Employees",
        "Airports",
        "Airplanes",
        "Crews",
        "Shifts",
        "Flights",
        "Passengers",
        "Buys",
        "Tickets",
    ):
        assert model_name in content
