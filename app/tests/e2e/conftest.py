import os

import pytest
from playwright.sync_api import Page


def login(page: Page, base_url: str, username: str, password: str) -> None:
    page.goto(f"{base_url}/login/")
    page.get_by_label("USERID").fill(username)
    page.get_by_label("PASSWORD").fill(password)
    page.get_by_role("button", name="LOGIN").click()


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")


@pytest.fixture(scope="session")
def browser_type_launch_args() -> dict[str, str]:
    executable = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH")
    return {"executable_path": executable} if executable else {}


@pytest.fixture
def sales_page(page: Page, base_url: str) -> Page:
    login(page, base_url, "10000006", "kxXRk7GIHw")
    page.get_by_role("heading", name="Search flight").wait_for()
    return page
