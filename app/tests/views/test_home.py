from freezegun import freeze_time


@freeze_time("2026-09-11 10:30:00")
def test_home_page(client, django_user_model):
    user = django_user_model.objects.create_superuser("admin", password="admin-password")
    client.force_login(user)
    response = client.get("/")
    assert response.status_code == 200
    assert b"COBOL AIRLINES" in response.content
    assert b"Open administration" in response.content


@freeze_time("2026-09-11 10:30:00")
def test_home_header_uses_local_date(client, django_user_model):
    from django.utils import timezone

    user = django_user_model.objects.create_superuser("admin", password="admin-password")
    client.force_login(user)
    response = client.get("/")
    expected = timezone.localdate().strftime("%d/%m/%Y")
    assert expected.encode() in response.content


def test_anonymous_home_redirects_to_login(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response.url == "/login/?next=/"
