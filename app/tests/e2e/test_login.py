import pytest
from playwright.sync_api import Page, expect

from .conftest import login

pytestmark = pytest.mark.e2e


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("10000029", "8s1i3NL"),
        ("10000013", "VDNDY7xUpm25"),
        ("10000027", "1jok1x"),
        ("10000022", "8I324l"),
        ("10000003", "7bVHdRyqYD"),
        ("10000017", "fijshQ3d"),
    ],
)
def test_role_home(page: Page, base_url: str, username: str, password: str) -> None:
    login(page, base_url, username, password)
    unavailable = page.get_by_text("functions are not available yet", exact=False)
    menu_links = page.locator("nav.container a")
    assert unavailable.count() > 0 or menu_links.count() > 2


def test_bad_password_and_login_redirect(page: Page, base_url: str) -> None:
    login(page, base_url, "10000006", "wrong")
    expect(page.get_by_text("Password or userid incorrect.", exact=True)).to_be_visible()
    page.goto(f"{base_url}/sales/flights/")
    expect(page).to_have_url(f"{base_url}/login/?next=/sales/flights/")
