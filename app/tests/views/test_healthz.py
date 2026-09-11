import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_healthz_reports_database_status(client):
    response = client.get(reverse("healthz"))
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": True}
