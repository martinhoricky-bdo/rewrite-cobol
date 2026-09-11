from django.conf import settings

from config.settings import base


def test_timezone_setting():
    assert settings.TIME_ZONE == "Europe/Paris"


def test_custom_user_setting():
    assert settings.AUTH_USER_MODEL == "accounts.User"


def test_argon2_is_default_password_hasher():
    assert base.PASSWORD_HASHERS[0] == "django.contrib.auth.hashers.Argon2PasswordHasher"
