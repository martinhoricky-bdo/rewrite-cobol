from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from freezegun import freeze_time

from core.messages import E_AUTH_03


@pytest.fixture(autouse=True)
def empty_login_cache():
    cache.clear()
    yield
    cache.clear()


def _fail(client, username: str, ip: str = "192.0.2.10"):
    return client.post("/login/", {"username": username, "password": "incorrect"}, REMOTE_ADDR=ip)


def _user():
    return get_user_model().objects.create_user(username="limit001", password="correct-pass")


@pytest.mark.django_db
def test_eleventh_attempt_is_blocked_even_with_correct_password(client):
    user = _user()
    for _ in range(10):
        assert E_AUTH_03.split("{")[0] not in _fail(client, user.username).content.decode()

    response = client.post(
        "/login/",
        {"username": user.username, "password": "correct-pass"},
        REMOTE_ADDR="192.0.2.10",
    )

    assert response.status_code == 200
    assert E_AUTH_03.format(minutes=15) in response.content.decode()
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_login_succeeds_after_limiter_window_expires(client):
    user = _user()
    started = timezone.now()
    with freeze_time(started):
        for _ in range(10):
            _fail(client, user.username)

    with freeze_time(started + timedelta(minutes=16)):
        response = client.post(
            "/login/",
            {"username": user.username, "password": "correct-pass"},
            REMOTE_ADDR="192.0.2.10",
        )

    assert response.status_code == 302
    assert client.session["_auth_user_id"] == str(user.pk)


@pytest.mark.django_db
def test_successful_login_resets_failure_counter(client):
    user = _user()
    for _ in range(9):
        _fail(client, user.username)
    response = client.post(
        "/login/",
        {"username": user.username, "password": "correct-pass"},
        REMOTE_ADDR="192.0.2.10",
    )
    assert response.status_code == 302

    client.logout()
    for _ in range(9):
        _fail(client, user.username)
    response = client.post(
        "/login/",
        {"username": user.username, "password": "correct-pass"},
        REMOTE_ADDR="192.0.2.10",
    )
    assert response.status_code == 302
