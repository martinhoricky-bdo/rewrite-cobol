from freezegun import freeze_time


@freeze_time("2026-09-11 10:30:00")
def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"COBOL AIRLINES" in response.content
    assert b"Programming at heights" in response.content


@freeze_time("2026-09-11 10:30:00")
def test_home_header_uses_local_date(client):
    from django.utils import timezone

    response = client.get("/")
    expected = timezone.localdate().strftime("%d/%m/%Y")
    assert expected.encode() in response.content
